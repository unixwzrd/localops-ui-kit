import json

import pytest
from localops_ui.code_editor import EditorSnapshot
from localops_ui_testkit import assert_layout, measure_layout
from playwright.sync_api import expect


def load(page, repository_url):
    page.goto(f"{repository_url}/examples/component-gallery/code-editor.html")
    page.wait_for_function("Boolean(window.editorHarness)")


@pytest.mark.parametrize("viewport", [(1440, 900), (820, 1024), (390, 844)])
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_editor_layout_keyboard_reveal_and_wrap(page, repository_url, viewport, theme):
    page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
    load(page, repository_url)
    page.locator("html").evaluate("(node,t) => node.dataset.theme=t", theme)
    editor = page.get_by_role("textbox", name="Session draft")
    editor.focus()
    editor.press("Control+End")
    editor.press("Enter")
    editor.press_sequentially("literal <script>text</script> 😀")
    assert "😀" in editor.input_value()
    page.evaluate("editorHarness.revealLines({startLine:2,endLine:3},{focus:true})")
    expect(editor).to_be_focused()
    assert page.evaluate("editorHarness.getSnapshot().selection.end > editorHarness.getSnapshot().selection.start")
    editor.press("Tab")
    assert not editor.evaluate("node=>node===document.activeElement")
    page.get_by_label("Wrap lines").uncheck()
    page.get_by_label("Wrap lines").check()
    assert_layout(measure_layout(page, mode="static"), label=f"editor-{viewport}-{theme}")
    assert_layout(measure_layout(page, mode="reachability"), label=f"editor-reachable-{viewport}-{theme}")


def test_editor_transactions_revisions_unicode_and_states(page, repository_url):
    load(page, repository_url)
    result = page.evaluate(r"""() => {
      const c=editorHarness;
      c.setDocument({id:'document-b',revision:1,text:'😀 one\none',readOnly:false});
      c.setSelection({start:3,end:6}); c.replaceSelection('one','two');
      c.replaceAll('one','three'); const changed=c.getSnapshot().text;
      c.undo(); c.undo(); const original=c.getSnapshot().text;
      c.redo(); c.redo(); c.setSelection({start:0,end:c.input.value.length}); c.indent();
      c.undo(); const undoneIndent=c.getSnapshot().text;
      let errors=0;
      for(const fn of [()=>c.setSelection({start:1,end:2}),
        ()=>c.setDocument({id:'document-b',revision:1,text:'other',readOnly:false}),
        ()=>c.setDocument({id:'document-c',revision:1,text:'other',readOnly:false})]) {
        try {fn();} catch {errors++;}
      }
      c.setDocument({id:'document-b',revision:2,text:'😀 one\none',readOnly:false});
      const preserved=c.getSnapshot().text===changed;
      const detached=c.getSnapshot(); detached.selection.start=999; detached.text='mutated';
      c.setState({kind:'unavailable',message:'Synthetic unavailable'});
      try {c.replaceAll('two','x');}catch{errors++;}
      const readonly=c.getSnapshot().readOnly;
      c.setState({kind:'ready'}); c.revert(); const reverted=c.getSnapshot().text;
      c.setDocument({id:'document-c',revision:1,text:'fresh',readOnly:true},{discardChanges:true});
      return {changed,original,undoneIndent,errors,preserved,readonly,reverted,snapshot:c.getSnapshot()};
    }""")
    assert result["changed"] == "😀 two\nthree"
    assert result["original"] == result["reverted"] == "😀 one\none"
    assert result["undoneIndent"] == result["changed"]
    assert result["errors"] == 4
    assert result["preserved"] and result["readonly"]
    EditorSnapshot.model_validate_json(json.dumps(result["snapshot"]))


def test_editor_ime_history_bounds_intents_and_cleanup(page, repository_url):
    load(page, repository_url)
    result = page.evaluate("""() => {
      const c=editorHarness;
      c.setDocument({id:'composition',revision:1,text:'',readOnly:false});
      c.input.dispatchEvent(new CompositionEvent('compositionstart'));
      c.input.value='に'; c.input.dispatchEvent(new InputEvent('input',{inputType:'insertCompositionText'}));
      c.input.value='日本😀'; c.input.dispatchEvent(new InputEvent('input',{inputType:'insertCompositionText'}));
      c.input.dispatchEvent(new CompositionEvent('compositionend'));
      const count=c.getSnapshot().history.undo; c.undo(); const undone=c.input.value; c.redo();
      c.limit={transactions:2,bytes:8388608};
      c.replaceAll('日','A'); c.replaceAll('本','B'); c.replaceAll('A','C');
      const bounded=c.getSnapshot().history;
      c.limit={transactions:2,bytes:1}; c.replaceAll('C','D'); const oversized=c.getSnapshot().history;
      c.controls.get('Copy').click(); c.controls.get('Export').click();
      const intent=window.copiedDraft.text===c.input.value && window.exportedDraft.text===c.input.value;
      c.destroy(); let destroyed=false;try{c.getSnapshot();}catch{destroyed=true;}
      return {count,undone,bounded,oversized,intent,destroyed};
    }""")
    assert result["count"] == 1 and result["undone"] == ""
    assert result["bounded"]["undo"] == 2 and result["bounded"]["discardedTransactions"] > 0
    assert result["oversized"]["undo"] == 0 and result["oversized"]["bytes"] == 0
    assert result["intent"] and result["destroyed"]


def test_editor_native_history_readonly_bounds_and_wrapped_gutter(page, repository_url):
    load(page, repository_url)
    editor = page.get_by_role("textbox", name="Session draft")
    editor.fill("abc")
    editor.press_sequentially("😀")
    editor.press("Control+z")
    assert editor.input_value() == "abc"
    editor.press("Control+Shift+z")
    assert "😀" in editor.input_value()
    result = page.evaluate(r"""() => {
      const c=editorHarness;
      c.setDocument({id:'wrap',revision:1,text:'long '.repeat(2000)+'\nnext',readOnly:false},{discardChanges:true});
      const height=c.gutter.firstChild.getBoundingClientRect().height;
      c.revealLines({startLine:2,endLine:2}); const revealed=c.input.scrollTop;
      c.setDocument({id:'wrap',revision:2,text:c.document.text,readOnly:true});
      c.input.dispatchEvent(new KeyboardEvent('keydown',{key:'z',ctrlKey:true,cancelable:true}));
      const original=c.input.value;let errors=0;
      for(const fn of [()=>c.replaceAll('long','short'),
        ()=>c.setDocument({id:'bounds',revision:1,text:'x'.repeat(1048577),readOnly:false}),
        ()=>c.setDocument({id:'bounds',revision:1,text:'x\r\n',readOnly:false}),
        ()=>c.revealLines({startLine:0,endLine:1})]){try{fn();}catch{errors++;}}
      return {height,revealed,errors,unchanged:c.input.value===original};
    }""")
    assert result["height"] > 21 and result["revealed"] > 0
    assert result["errors"] == 4 and result["unchanged"]


def test_editor_restores_consumer_draft_without_rebasing(page, repository_url):
    load(page, repository_url)
    result = page.evaluate("""() => {
      const c=editorHarness;
      c.setDocument({id:'cached',revision:3,text:'original',readOnly:false});
      c.setDraft({documentId:'cached',revision:3,text:'changed',selection:{start:0,end:7}});
      const dirty=c.getSnapshot().dirty;
      let errors=0;
      for(const draft of [
        {documentId:'cached',revision:2,text:'bad',selection:{start:0,end:1}},
        {documentId:'cached',revision:3,text:'bad',selection:{start:0,end:99}}]) {
        try{c.setDraft(draft);}catch{errors++;}
      }
      const retained=c.input.value; c.revert();const original=c.input.value;c.undo();
      return {dirty,errors,retained,original,undone:c.input.value};
    }""")
    assert result == {"dirty": True, "errors": 2, "retained": "changed", "original": "original", "undone": "changed"}
