import pytest
from localops_ui_testkit import assert_layout, measure_layout
from playwright.sync_api import expect


def load_shell(page, repository_url):
    page.goto(f"{repository_url}/examples/component-gallery/")
    page.evaluate(
        """async url => {
          const {operatorShell, button} = await import(url);
          const destination = button({label:'Destination control'});
          let shell;
          shell = operatorShell({title:'Navigation harness',content:destination,navigation:[
            {id:'browse',label:'Browse'},
            {id:'connections',label:'Connections',onSelect:() => {
              window.navigationFocus = document.activeElement;
              destination.textContent = 'Connections control';
              shell.closeNavigation({focusTarget:destination});
            }}]});
          document.body.replaceChildren(shell);
          window.shellHarness = {shell,destination};
        }""",
        f"{repository_url}/packages/web/static/index.js",
    )


@pytest.mark.parametrize("viewport", [(1440, 900), (820, 1024), (390, 844)])
@pytest.mark.parametrize("theme", ["light", "dark"])
@pytest.mark.parametrize("activation", ["pointer", "keyboard"])
def test_shell_accepted_navigation_closes_drawer(page, repository_url, viewport, theme, activation):
    page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
    load_shell(page, repository_url)
    page.locator("html").evaluate("(node, theme) => node.dataset.theme = theme", theme)
    toggle = page.get_by_role("button", name="Toggle navigation", include_hidden=True)
    link = page.get_by_role("link", name="Connections", exact=True)
    if viewport[0] == 390:
        if activation == "keyboard":
            toggle.focus()
            toggle.press("Enter")
        else:
            toggle.click()
    if activation == "keyboard":
        link.focus()
        link.press("Enter")
    else:
        link.click()
    destination = page.get_by_role("button", name="Connections control")
    expect(destination).to_be_visible()
    expect(toggle).to_have_attribute("aria-expanded", "false")
    if viewport[0] == 390:
        expect(destination).to_be_focused()
        expect(link).to_be_hidden()
    else:
        expect(link).to_be_visible()
        assert page.evaluate("document.activeElement === navigationFocus")
        if activation == "keyboard":
            expect(link).to_be_focused()
    assert_layout(measure_layout(page, mode="static"), label=f"closed-shell-{viewport}-{theme}")
    assert_layout(measure_layout(page, mode="reachability"), label=f"reachable-shell-{viewport}-{theme}")
    before = page.evaluate("document.activeElement.tagName")
    assert not page.evaluate("shellHarness.shell.closeNavigation()")
    assert page.evaluate("document.activeElement.tagName") == before
    destination.click()


def test_shell_passive_updates_default_focus_and_invalid_target(page, repository_url):
    page.set_viewport_size({"width": 390, "height": 844})
    load_shell(page, repository_url)
    toggle = page.get_by_role("button", name="Toggle navigation")
    toggle.click()
    link = page.get_by_role("link", name="Browse", exact=True)
    link.focus()
    page.evaluate("shellHarness.destination.textContent = 'Passive update'")
    expect(toggle).to_have_attribute("aria-expanded", "true")
    expect(link).to_be_focused()
    assert page.evaluate("""() => {
      try {shellHarness.shell.closeNavigation({focusTarget:document.body});return false;}
      catch {return true;}
    }""")
    expect(toggle).to_have_attribute("aria-expanded", "true")
    assert page.evaluate("shellHarness.shell.closeNavigation()")
    expect(page.get_by_role("main")).to_be_focused()
    expect(link).to_be_hidden()
    toggle.click()
    page.evaluate("shellHarness.destination.focus(); shellHarness.shell.closeNavigation()")
    expect(page.get_by_role("button", name="Passive update")).to_be_focused()
