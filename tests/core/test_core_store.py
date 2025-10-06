from core.store import InMemoryCoreStore, CoreMemoryItem


def test_store_upsert_and_get_by_id():
    store = InMemoryCoreStore()
    item = CoreMemoryItem(id="1", level="semantic", key="prefers_mornings", value={"fact": "no meetings before 11am"})
    store.upsert(item)
    got = store.get_by_id("1")
    assert got is not None
    assert got.value["fact"] == "no meetings before 11am"


def test_store_get_by_key_filters_and_sorts():
    store = InMemoryCoreStore()
    store.upsert(CoreMemoryItem(id="a", level="semantic", key="k", value={}))
    store.upsert(CoreMemoryItem(id="b", level="semantic", key="k", value={}))
    res = store.get_by_key("k", level="semantic")
    assert len(res) == 2
