"""Serve never crashes into a bad artifact: tampering is a miss, and a miss is the fallback."""

from agentic_compiler import Store, load_case, serve, walk


def test_tampered_artifact_is_a_miss(tmp_path):
    res = walk(load_case("accept/copy_nvidia.case.json"), tmp_path)
    store = Store(res.out_dir / "store")
    art = serve(store, res.cache_key_digest).artifact_path
    art.write_text(art.read_text() + "\n// tampered\n")
    got = serve(store, res.cache_key_digest)
    assert not got.hit and got.fallback == "classical"
