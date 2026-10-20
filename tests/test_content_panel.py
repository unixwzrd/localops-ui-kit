import json

import pytest
from localops_ui.models import ContentPanelState
from localops_ui_testkit import assert_layout, measure_layout
from playwright.sync_api import expect


def load(page, repository_url):
    page.goto(f"{repository_url}/examples/component-gallery/content-panel.html")
    page.wait_for_function("Boolean(window.panelHarness)")


@pytest.mark.parametrize("viewport", [(1440, 900), (820, 1024), (390, 844)])
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_panel_layout_expansion_content_and_escape(page, repository_url, viewport, theme):
    page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
    load(page, repository_url)
    page.locator("html").evaluate("(node,theme)=>node.dataset.theme=theme", theme)
    opener = page.get_by_role("button", name="Open help")
    opener.focus()
    opener.press("Enter")
    dialog = page.get_by_role("dialog", name="Document help")
    expect(page.get_by_role("heading", name="Document help")).to_be_focused()
    assert dialog.get_attribute("aria-modal") == "true"
    assert dialog.get_attribute("aria-describedby")
    page.get_by_role("textbox", name="Panel note").fill("User note")
    for expanded in (False, True, False):
        page.evaluate("value=>panelHarness.panel.setExpanded(value)", expanded)
        width = dialog.bounding_box()["width"]
        assert abs(width - (viewport[0] if expanded else min(672, viewport[0]))) < 2
        assert page.evaluate("panelHarness.documentContent===panelHarness.panel.content.firstChild")
        expect(page.get_by_role("textbox", name="Panel note")).to_have_value("User note")
        assert_layout(measure_layout(page, mode="static"), label=f"panel-{viewport}-{theme}-{expanded}")
        assert_layout(measure_layout(page, mode="reachability"), label=f"panel-reachable-{viewport}-{theme}-{expanded}")
    page.keyboard.press("Escape")
    expect(dialog).to_be_hidden()
    expect(opener).to_be_focused()
    expect(page.get_by_role("textbox", name="Underlying draft")).to_have_value("Unchanged draft text")
    opener.click()
    expect(page.get_by_role("textbox", name="Panel note")).to_have_value("User note")
    page.get_by_role("button", name="Close", exact=True).click()
    expect(opener).to_be_focused()


def test_panel_focus_boundary_missing_opener_and_idempotence(page, repository_url):
    load(page, repository_url)
    page.get_by_role("button", name="Open help").click()
    page.get_by_role("link", name="Supplied link").focus()
    page.keyboard.press("Tab")
    expect(page.get_by_role("button", name="Expand", exact=True)).to_be_focused()
    page.keyboard.press("Shift+Tab")
    expect(page.get_by_role("link", name="Supplied link")).to_be_focused()
    result = page.evaluate("""() => {
      const h=panelHarness;h.draft.focus();const contained=h.panel.root.contains(document.activeElement);
      const reopened=h.panel.open(); h.opener.remove(); const closed=h.panel.close(); const repeated=h.panel.close();
      return {contained,reopened,closed,repeated,state:h.panel.getState(),changes:h.changes};
    }""")
    assert result["contained"] and not result["reopened"] and result["closed"] and not result["repeated"]
    assert result["changes"] == [{"open": True}, {"open": False}]
    ContentPanelState.model_validate_json(json.dumps(result["state"]))
    expect(page.get_by_role("button", name="Return destination")).to_be_focused()


def test_panel_safe_text_supplied_states_cleanup_and_validation(page, repository_url):
    load(page, repository_url)
    result = page.evaluate("""() => {
      const p=panelHarness.panel;let invalid=0;
      for(const fn of [()=>p.setContent({html:'bad'}),()=>p.setExpanded(1),()=>p.open({unexpected:true})]){
        try{fn();}catch{invalid++;}
      }
      p.setContent('<script>window.panelUnsafe=true</script><img src=x onerror="window.panelUnsafe=true">');
      p.open({opener:panelHarness.opener});
      const literal=p.content.textContent;const safe=!window.panelUnsafe;
      p.close();p.setContent('Loading supplied content');p.open();
      p.setContent('Consumer-supplied recoverable error');
      const message=p.content.textContent;p.destroy();let destroyed=false;
      try{p.open();}catch{destroyed=true;}
      return {invalid,literal,safe,message,destroyed,removed:!p.root.isConnected};
    }""")
    assert result["invalid"] == 3 and result["safe"] and result["destroyed"] and result["removed"]
    assert result["literal"].startswith("<script>")
    assert result["message"] == "Consumer-supplied recoverable error"


def test_panel_initial_focus_default_fallback_and_content_update(page, repository_url):
    load(page, repository_url)
    result = page.evaluate(
        """async url => {
          const {ContentPanel}=await import(url);
          const input=document.createElement('input');input.setAttribute('aria-label','Initial target');
          input.value='retained';
          const p=new ContentPanel({id:'second-panel',title:'Second panel',content:input});
          p.open({opener:panelHarness.opener,initialFocus:input}); const initial=document.activeElement===input;
          p.setContent('Loading'); const fallback=document.activeElement===p.title;
          p.setContent(input); const retained=input.value==='retained';
          panelHarness.opener.remove(); p.close();
          const returned=document.activeElement===document.querySelector('main');
          p.destroy();return {initial,fallback,retained,returned};
        }""",
        f"{repository_url}/packages/web/static/index.js",
    )
    assert result == {"initial": True, "fallback": True, "retained": True, "returned": True}


def test_panel_nested_native_focus_scroll_and_selection_retention(page, repository_url):
    load(page, repository_url)
    result = page.evaluate(
        """async url => {
          const {ContentPanel}=await import(url);const h=panelHarness;const p=h.panel;
          p.open({opener:h.opener}); p.content.scrollTop=100;
          const text=p.content.querySelector('p').firstChild;
          const range=document.createRange();range.setStart(text,0);range.setEnd(text,10);
          getSelection().removeAllRanges();getSelection().addRange(range);
          const selected=getSelection().toString();p.setExpanded(true);p.setExpanded(false);
          const selectionRetained=getSelection().toString()===selected;
          const position=p.content.scrollTop;p.close();p.open({opener:h.opener});
          const scrollRetained=p.content.scrollTop===position;
          const child=new ContentPanel({id:'nested',title:'Nested panel',content:'Nested supplied content'});
          child.open({opener:p.closeButton});const childFocused=child.root.contains(document.activeElement);
          child.close();const returnedToParent=document.activeElement===p.closeButton && p.root.open;
          child.destroy();p.close();const returnedToOpener=document.activeElement===h.opener;
          return {selectionRetained,scrollRetained,childFocused,returnedToParent,returnedToOpener};
        }""",
        f"{repository_url}/packages/web/static/index.js",
    )
    assert all(result.values()), result


@pytest.mark.parametrize("viewport", [(1440, 900), (820, 1024), (390, 844)])
def test_panel_single_escape_closes_populated_search(page, repository_url, viewport):
    page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
    load(page, repository_url)
    page.evaluate("""() => {
      const search=document.createElement('input');search.type='search';
      search.setAttribute('aria-label','Topic search');
      panelHarness.panel.setContent(search);panelHarness.panel.open({opener:panelHarness.opener});
    }""")
    search = page.get_by_role("searchbox", name="Topic search")
    search.fill("populated query")
    search.press("Escape")
    expect(page.get_by_role("dialog", name="Document help")).to_be_hidden()
    expect(page.get_by_role("button", name="Open help")).to_be_focused()
    assert page.evaluate("panelHarness.panel.content.querySelector('input').value") == "populated query"
    assert page.evaluate("panelHarness.changes") == [{"open": True}, {"open": False}]


def test_panel_escape_preserves_composition_and_modified_shortcuts(page, repository_url):
    load(page, repository_url)
    result = page.evaluate("""() => {
      const p=panelHarness.panel;const input=document.createElement('input');input.type='search';input.value='query';
      p.setContent(input);p.open({opener:panelHarness.opener});input.focus();
      const allowed=[];
      const variants=[{ctrlKey:true},{altKey:true},{metaKey:true},{shiftKey:true},{isComposing:true},{keyCode:229}];
      for(const options of variants) {
        const event=new KeyboardEvent('keydown',{key:'Escape',bubbles:true,cancelable:true,...options});
        input.dispatchEvent(event);allowed.push(!event.defaultPrevented && p.root.open);
      }
      input.dispatchEvent(new CompositionEvent('compositionstart',{bubbles:true}));
      const composingKey=new KeyboardEvent('keydown',{key:'Escape',bubbles:true,cancelable:true});
      input.dispatchEvent(composingKey);p.root.dispatchEvent(new Event('cancel',{cancelable:true}));
      const composingRetained=p.root.open && !composingKey.defaultPrevented;
      input.dispatchEvent(new CompositionEvent('compositionend',{bubbles:true}));
      const key=new KeyboardEvent('keydown',{key:'Escape',bubbles:true,cancelable:true});input.dispatchEvent(key);
      const closed=!p.root.open && key.defaultPrevented;
      return {allowed,composingRetained,closed,value:input.value,changes:panelHarness.changes};
    }""")
    assert all(result["allowed"]) and result["composingRetained"] and result["closed"]
    assert result["value"] == "query" and result["changes"] == [{"open": True}, {"open": False}]


def test_panel_search_escape_closes_only_dom_nested_child(page, repository_url):
    load(page, repository_url)
    page.evaluate(
        """async url => {
          const {ContentPanel}=await import(url);const parent=panelHarness.panel;
          parent.open({opener:panelHarness.opener});
          const input=document.createElement('input');input.type='search';
          input.setAttribute('aria-label','Nested search');
          const child=new ContentPanel({id:'nested-search-panel',title:'Nested search panel',content:input});
          parent.content.append(child.root);child.open({opener:parent.closeButton});window.nestedPanel=child;
        }""",
        f"{repository_url}/packages/web/static/index.js",
    )
    search = page.get_by_role("searchbox", name="Nested search")
    search.fill("nested query")
    search.press("Escape")
    expect(page.get_by_role("dialog", name="Nested search panel")).to_be_hidden()
    expect(page.get_by_role("dialog", name="Document help")).to_be_visible()
    expect(page.get_by_role("button", name="Close", exact=True)).to_be_focused()
    page.keyboard.press("Escape")
    expect(page.get_by_role("button", name="Open help")).to_be_focused()
