import { ResultReader, operatorShell } from "../../packages/web/static/index.js";

const results = Array.from({length: 60}, (_, i) => ({id: `result-${i}`, title: `Record ${i}`, excerpt: "Synthetic result description"}));
const blocks = Array.from({length: 80}, (_, i) => ({id: `block-${i}`, text: `${i}: Synthetic reading text. `.repeat(15)}));
blocks[1].text = '<script>window.readerUnsafe = true</script><img src=x onerror="window.readerUnsafe=true">';
blocks[2].text = "x".repeat(180);
let revision = 0;
let generation = 0;
const controller = new ResultReader({
    id: "reading-workspace", resultsLabel: "Results", readerLabel: "Reader", openLabel: "Open reader",
    returnLabel: "Return to results", emptyLabel: "No results", unselectedLabel: "No document selected",
    loadingLabel: "Loading", errorLabel: "Could not load", unavailableLabel: "Document unavailable", retryLabel: "Retry",
    onSelect: async (resultId) => {
        const request = ++generation;
        revision = Math.max(revision, controller.snapshot.revision);
        controller.setSnapshot({revision: ++revision, results, selectedResultId: resultId,
            reader: {kind: "loading", resultId, message: "Loading selected content"}});
        // Injected fixture delay; demonstrates consumer-owned obsolete-load cancellation.
        await new Promise((resolve) => setTimeout(resolve, resultId === "result-0" ? 120 : 5));
        if (request !== generation) return;
        const blockId = `block-${Number(resultId.split("-")[1])}`;
        revision = Math.max(revision, controller.snapshot.revision);
        controller.setSnapshot({revision: ++revision, results, selectedResultId: resultId,
            reader: {kind: "ready", resultId, id: "document-a", contentRevision: 1, title: "Synthetic document", blocks}});
        controller.revealBlock({documentId: "document-a", contentRevision: 1, blockId});
    },
    onRetry: (resultId) => controller.options.onSelect(resultId),
});
document.body.append(operatorShell({title: "Reading harness", navigation: [{id: "reading", label: "Reading"}], content: controller.root}));
controller.setSnapshot({revision: revision++, results, selectedResultId: null, reader: {kind: "unselected"}});
// Test harness access only; production consumers retain their own controller reference.
window.readerHarness = controller;
