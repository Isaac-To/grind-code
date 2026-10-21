"""grind.store — persistence behavior."""
from __future__ import annotations

import json

from grind import store


def test_load_fresh_returns_complete_defaults(state):
    assert set(state) == {"config", "cards", "logs", "session"}
    assert state["cards"] == {} and state["logs"] == [] and state["session"] is None
    cfg = state["config"]
    assert cfg["daily_new"] == 5
    assert cfg["targets"] == {"Easy": 15, "Medium": 30, "Hard": 45}
    assert cfg["retention_target"] == 0.9
    assert cfg["auto_web"] is False and cfg["auto_edit"] is False


def test_save_then_load_roundtrip(state, env):
    state["cards"]["two-sum"] = {"stability": 1.5}
    state["config"]["daily_new"] = 9
    store.save(state)
    loaded = store.load()
    assert loaded["cards"]["two-sum"] == {"stability": 1.5}
    assert loaded["config"]["daily_new"] == 9


def test_save_is_atomic_no_tmp_left_behind(state, env):
    store.save(state)
    data_dir = store.data_dir()
    assert (data_dir / "state.json").exists()
    assert not (data_dir / "state.tmp").exists()
    assert json.loads((data_dir / "state.json").read_text())["config"]["daily_new"] == 5


def test_old_state_gains_new_default_config_keys(env, tmp_path):
    # simulate a state written before auto_web/auto_edit existed
    data = store.data_dir()
    data.mkdir(parents=True)
    (data / "state.json").write_text(json.dumps({
        "config": {"daily_new": 3}, "cards": {}, "logs": [], "session": None}))
    loaded = store.load()
    assert loaded["config"]["daily_new"] == 3          # user value preserved
    assert loaded["config"]["auto_web"] is False       # new key backfilled
    assert loaded["config"]["retention_target"] == 0.9


def test_data_dir_respects_env_override(env):
    assert str(store.data_dir()).endswith("data")
    assert str(store.state_path()) == str(store.data_dir() / "state.json")


def test_save_creates_data_dir_if_missing(env):
    assert not store.state_path().exists()
    store.save(store.load())
    assert store.state_path().exists()
