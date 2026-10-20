import pytest
from localops_ui_testkit import assert_layout, measure_layout
from playwright.sync_api import expect


def load(page, repository_url):
    page.goto(f"{repository_url}/examples/component-gallery/result-reader.html")
    page.wait_for_function("Boolean(window.readerHarness)")


@pytest.mark.parametrize("viewport", [(1440, 900), (820, 1024), (390, 844)])
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_reader_layout_navigation_and_safety(page, repository_url, viewport, theme):
    page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
    load(page, repository_url)
    page.locator("html").evaluate("(node, theme) => node.dataset.theme = theme", theme)
    result = page.locator('[data-result-id="result-1"]')
    result.focus()
    result.press("Enter")
    page.wait_for_function("readerHarness.snapshot.reader.kind === 'ready'")
    if viewport[0] == 1440:
        expect(result).to_be_focused()
    else:
        expect(page.locator("#reading-workspace-reader-title")).to_be_focused()
    expect(page.locator('[data-block-id="block-1"]')).to_contain_text("<script>")
    assert not page.evaluate("Boolean(window.readerUnsafe)")
    assert_layout(measure_layout(page, mode="static"), label=f"reader-{viewport}-{theme}")
    assert_layout(measure_layout(page, mode="reachability"), label=f"reader-reachable-{viewport}-{theme}")
    page.get_by_role("button", name="Return to results").click()
    expect(result).to_be_focused()
    page.locator('[data-result-id="result-59"]').click()
    page.wait_for_function(
        "readerHarness.snapshot.reader.kind === 'ready' && readerHarness.snapshot.selectedResultId === 'result-59'"
    )
    before = page.evaluate(
        "readerHarness.resultsPane.hidden ? readerHarness.resultPosition : readerHarness.resultsScroll.scrollTop"
    )
    page.get_by_role("button", name="Return to results").click()
    assert page.evaluate("readerHarness.resultsScroll.scrollTop") == before
    expect(page.locator('[data-result-id="result-59"]')).to_be_focused()


def test_reader_passive_update_explicit_reveal_and_atomic_rejection(page, repository_url):
    load(page, repository_url)
    page.locator('[data-result-id="result-1"]').click()
    page.wait_for_function("readerHarness.snapshot.reader.kind === 'ready'")
    result = page.evaluate("""() => {
      const c = readerHarness;
      const block = c.blocks.get('block-1');
      const range = document.createRange(); range.selectNodeContents(block);
      getSelection().removeAllRanges(); getSelection().addRange(range);
      c.readerScroll.scrollTop = 750;
      const previousScroll = c.readerScroll.scrollTop;
      const focus = document.activeElement;
      c.setSnapshot({...c.snapshot, revision: c.snapshot.revision + 1});
      const retained = c.blocks.get('block-1') === block && c.readerScroll.scrollTop === previousScroll
        && document.activeElement === focus && getSelection().toString().includes('<script>');
      c.revealBlock({documentId:'document-a', contentRevision:1, blockId:'block-60'});
      const revealed = c.readerScroll.scrollTop > previousScroll && document.activeElement === focus;
      const html = c.root.innerHTML;
      let errors = 0;
      for (const update of [c.snapshot,
        {...c.snapshot, revision:c.snapshot.revision+1, reader:{...c.snapshot.reader, resultId:'result-2'}},
        {...c.snapshot, revision:c.snapshot.revision+1,
          reader:{...c.snapshot.reader, blocks:[{id:'block-1',text:'changed'}]}}]) {
        try {c.setSnapshot(update);} catch {errors++;}
      }
      try {c.revealBlock({documentId:'document-a',contentRevision:2,blockId:'block-1'});} catch {errors++;}
      return {retained,revealed,errors,unchanged:c.root.innerHTML===html};
    }""")
    assert result == {"retained": True, "revealed": True, "errors": 4, "unchanged": True}


def test_reader_same_document_match_hidden_reveal_and_resize(page, repository_url):
    page.set_viewport_size({"width": 390, "height": 844})
    load(page, repository_url)
    page.locator('[data-result-id="result-1"]').click()
    page.wait_for_function("readerHarness.snapshot.reader.kind === 'ready'")
    page.evaluate("window.originalBlock = readerHarness.blocks.get('block-1')")
    page.get_by_role("button", name="Return to results").click()
    page.evaluate("readerHarness.options.onSelect('result-50')")
    page.wait_for_function("readerHarness.snapshot.reader.kind === 'ready'")
    page.get_by_role("button", name="Open reader").click()
    assert page.evaluate("readerHarness.blocks.get('block-1') === originalBlock")
    assert page.evaluate("readerHarness.readerScroll.scrollTop > 1000")
    page.set_viewport_size({"width": 1440, "height": 900})
    page.wait_for_function(
        "!readerHarness.narrow && !readerHarness.resultsPane.hidden && !readerHarness.readerPane.hidden"
    )
    expect(page.locator("#reading-workspace-reader-title")).to_be_focused()
    page.locator('[data-result-id="result-50"]').focus()
    expect(page.locator('[data-result-id="result-50"]')).to_be_focused()
    page.set_viewport_size({"width": 390, "height": 844})
    expect(page.locator('[data-result-id="result-50"]')).to_be_visible()
    page.wait_for_function("readerHarness.readerPane.hidden")
    assert page.evaluate("readerHarness.readerPane.hidden")


def test_reader_removed_focus_and_new_document_start(page, repository_url):
    load(page, repository_url)
    page.locator('[data-result-id="result-1"]').focus()
    page.evaluate("""() => {const c=readerHarness;c.setSnapshot({...c.snapshot,revision:c.snapshot.revision+1,
      results:c.snapshot.results.filter(r=>r.id!=='result-1')});}""")
    expect(page.locator('[data-result-id="result-2"]')).to_be_focused()
    page.locator('[data-result-id="result-3"]').click()
    page.wait_for_function("readerHarness.snapshot.reader.kind === 'ready'")
    page.evaluate("""() => {const c=readerHarness;c.readerScroll.scrollTop=1500;
      c.returnToResults(); c.setSnapshot({...c.snapshot,revision:c.snapshot.revision+1,
        reader:{...c.snapshot.reader,id:'document-b',contentRevision:2}}); c.openReader();}""")
    assert page.evaluate("readerHarness.readerScroll.scrollTop") == 0


def test_reader_obsolete_load_states_and_destroy(page, repository_url):
    load(page, repository_url)
    page.evaluate("readerHarness.options.onSelect('result-0'); readerHarness.options.onSelect('result-1')")
    page.wait_for_function("readerHarness.snapshot.reader.kind === 'ready'")
    page.wait_for_timeout(160)
    assert page.evaluate("readerHarness.snapshot.selectedResultId") == "result-1"
    for kind, label in [("error", "Could not load"), ("unavailable", "Document unavailable")]:
        page.evaluate(
            """kind => {const c=readerHarness;c.setSnapshot({...c.snapshot,revision:c.snapshot.revision+1,
          reader:{kind,resultId:'result-1',message:'Synthetic failure',retryAvailable:true}})}""",
            kind,
        )
        expect(page.get_by_role("heading", name=label)).to_be_visible()
        expect(page.get_by_role("button", name="Retry")).to_be_visible()
    page.get_by_role("button", name="Retry").click()
    page.wait_for_function("readerHarness.snapshot.reader.kind === 'ready'")
    page.evaluate("""() => {const c=readerHarness;c.setSnapshot({revision:c.snapshot.revision+1,results:[],
      selectedResultId:null,reader:{kind:'unselected'}})}""")
    expect(page.get_by_role("heading", name="No results")).to_be_visible()
    assert page.evaluate(
        """() => {const c=readerHarness;c.destroy();try {c.returnToResults();return false;}catch{return true;}}"""
    )
