import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from .models import LayoutReport


@dataclass(frozen=True, slots=True)
class OracleSelectors:
    panes: str = "[data-layout-pane]"
    controls: str = "button, input, select, textarea, a[href], summary, [tabindex]:not([tabindex='-1'])"
    labels: str = "label, [data-layout-label]"
    modals: str = "[role='dialog'][aria-modal='true']"


_ORACLE_SCRIPT = r"""
({ mode, selectors }) => {
  const tolerance = 2;
  const issues = [];
  const describe = (node) => {
    if (!node) return "<none>";
    const id = node.id ? `#${node.id}` : "";
    const classes = [...node.classList].slice(0, 3).map((name) => `.${name}`).join("");
    return `${node.tagName.toLowerCase()}${id}${classes}`;
  };
  const visible = (node) => {
    if (node.closest("[hidden], [inert]")) return false;
    const closedDetails = node.closest("details:not([open])");
    if (closedDetails) {
      const summary = closedDetails.querySelector(":scope > summary");
      if (!summary || !summary.contains(node)) return false;
    }
    const style = getComputedStyle(node);
    const rect = node.getBoundingClientRect();
    return style.display !== "none" && style.visibility !== "hidden" && Number(style.opacity) !== 0 && rect.width > 0 && rect.height > 0;
  };
  const contains = (outer, inner) => outer === inner || outer.contains(inner);
  const modalRoots = [...document.querySelectorAll(selectors.modals)].filter(visible);
  const modalOpen = modalRoots.length > 0;
  const inModal = (node) => modalRoots.some((root) => contains(root, node));
  const modalBlockers = [...new Set(modalRoots.flatMap((root) => {
    const blockers = [root];
    for (let parent = root.parentElement; parent && parent !== document.body; parent = parent.parentElement) {
      const rect = parent.getBoundingClientRect();
      if (getComputedStyle(parent).position === "fixed" && rect.left <= tolerance && rect.top <= tolerance && rect.right >= innerWidth - tolerance && rect.bottom >= innerHeight - tolerance) blockers.push(parent);
    }
    return blockers;
  }))];
  const panes = [...document.querySelectorAll(selectors.panes)].filter(visible);

  if (document.documentElement.scrollWidth > innerWidth + tolerance) {
    issues.push({ kind: "document-overflow", target: "html", detail: { scrollWidth: document.documentElement.scrollWidth, viewportWidth: innerWidth } });
  }
  for (const pane of panes) {
    const style = getComputedStyle(pane);
    const overflowXAllowed = ["auto", "scroll"].includes(style.overflowX);
    const overflowYAllowed = ["auto", "scroll"].includes(style.overflowY);
    if (pane.scrollWidth > pane.clientWidth + tolerance && !overflowXAllowed) {
      issues.push({ kind: "pane-overflow", target: describe(pane), detail: { axis: "x", client: pane.clientWidth, scroll: pane.scrollWidth } });
    }
    if (pane.scrollHeight > pane.clientHeight + tolerance && !overflowYAllowed) {
      issues.push({ kind: "pane-overflow", target: describe(pane), detail: { axis: "y", client: pane.clientHeight, scroll: pane.scrollHeight } });
    }
  }

  const overlays = [...document.querySelectorAll("body *")].filter((node) => {
    if (!visible(node)) return false;
    const position = getComputedStyle(node).position;
    return position === "fixed" || position === "sticky";
  });
  const controls = [...document.querySelectorAll(selectors.controls)].filter((node) => visible(node) && !node.disabled);
  const pointsFor = (rect) => [
    [rect.left + rect.width / 2, rect.top + rect.height / 2, "center"],
    [rect.left + Math.min(6, rect.width / 4), rect.top + Math.min(6, rect.height / 4), "top-left-inset"],
    [rect.right - Math.min(6, rect.width / 4), rect.bottom - Math.min(6, rect.height / 4), "bottom-right-inset"],
  ];

  for (const control of controls) {
    const backgroundControl = modalOpen && !inModal(control);
    if (mode === "reachability" && !backgroundControl) control.scrollIntoView({ block: "center", inline: "nearest" });
    const rect = control.getBoundingClientRect();
    const inside = rect.left >= -tolerance && rect.top >= -tolerance && rect.right <= innerWidth + tolerance && rect.bottom <= innerHeight + tolerance;
    if (mode === "reachability" && !inside) {
      issues.push({ kind: "unreachable-control", target: describe(control), detail: { left: rect.left, top: rect.top, right: rect.right, bottom: rect.bottom } });
      continue;
    }
    if (!inside) continue;
    if (backgroundControl) {
      for (const [x, y, point] of pointsFor(rect)) {
        const hit = document.elementFromPoint(x, y);
        if (hit && modalBlockers.some((blocker) => contains(blocker, hit))) continue;
        issues.push({ kind: "modal-background-operable", target: describe(control), detail: { point, hit: describe(hit) } });
        break;
      }
      continue;
    }
    for (const [x, y, point] of pointsFor(rect)) {
      const hit = document.elementFromPoint(x, y);
      if (hit && (contains(control, hit) || contains(hit, control))) continue;
      issues.push({ kind: "hit-test", target: describe(control), detail: { point, blockedBy: describe(hit) } });
      break;
    }
    for (const overlay of overlays) {
      if (contains(overlay, control) || contains(control, overlay)) continue;
      if (modalOpen && inModal(overlay) !== inModal(control)) continue;
      const other = overlay.getBoundingClientRect();
      const overlapWidth = Math.min(rect.right, other.right) - Math.max(rect.left, other.left);
      const overlapHeight = Math.min(rect.bottom, other.bottom) - Math.max(rect.top, other.top);
      if (overlapWidth > tolerance && overlapHeight > tolerance) {
        issues.push({ kind: "overlay-occlusion", target: describe(control), detail: { overlay: describe(overlay), overlapWidth, overlapHeight } });
      }
    }
  }

  for (const label of [...document.querySelectorAll(selectors.labels)].filter(visible)) {
    const style = getComputedStyle(label);
    const clipped = label.scrollWidth > label.clientWidth + tolerance && ["hidden", "clip"].includes(style.overflowX);
    if (clipped) issues.push({ kind: "clipped-label", target: describe(label), detail: { clientWidth: label.clientWidth, scrollWidth: label.scrollWidth } });
    const rect = label.getBoundingClientRect();
    const parent = label.parentElement?.getBoundingClientRect();
    if (parent && (rect.right > parent.right + tolerance || rect.bottom > parent.bottom + tolerance) && ["hidden", "clip"].includes(getComputedStyle(label.parentElement).overflow)) {
      issues.push({ kind: "permanent-clipping", target: describe(label), detail: { parent: describe(label.parentElement) } });
    }
  }

  return {
    viewport: { width: innerWidth, height: innerHeight },
    mode,
    modal: { open: modalOpen, roots: modalRoots.map(describe) },
    issues,
  };
}
"""


def measure_layout(
    page: Any,
    *,
    mode: Literal["static", "reachability"] = "static",
    selectors: OracleSelectors | None = None,
) -> LayoutReport:
    """Measure the current rendered page and return a validated public report."""
    selected = selectors or OracleSelectors()
    raw = page.evaluate(_ORACLE_SCRIPT, {"mode": mode, "selectors": asdict(selected)})
    return LayoutReport.model_validate_json(json.dumps(raw))


def assert_layout(report: LayoutReport, *, label: str = "layout") -> None:
    """Raise an evidence-rich assertion when any governed geometry check fails."""
    if report.issues:
        raise AssertionError(f"{label} failed:\n{json.dumps(report.model_dump(mode='json'), indent=2, sort_keys=True)}")


def write_report(report: LayoutReport, destination: Path) -> None:
    """Persist a validated JSON report without environment-specific metadata."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
