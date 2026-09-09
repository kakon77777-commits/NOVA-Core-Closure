import json
from pathlib import Path

import numpy as np

from nova_core.cli import main


def test_cli_interop_inspect_reports_numpy_tensor_contract(tmp_path, capsys):
    path = tmp_path / "x.npy"
    np.save(path, np.arange(6, dtype=np.float32).reshape(2, 3))
    rc = main(["interop", "inspect", str(path)])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "device": [1, 0],
        "dtype": "float32",
        "ok": True,
        "shape": [2, 3],
    }


def test_cli_interop_roundtrip_reports_zero_copy(tmp_path, capsys):
    path = tmp_path / "x.npy"
    np.save(path, np.arange(4, dtype=np.float64))
    rc = main(["interop", "roundtrip", str(path)])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["dtype"] == "float64"
    assert payload["shape"] == [4]
    assert payload["shared_memory"] is True
    assert payload["equal"] is True


def test_cli_interop_rejects_non_npy_input(tmp_path, capsys):
    path = tmp_path / "bad.txt"
    path.write_text("not-npy", encoding="utf-8")
    rc = main(["interop", "inspect", str(path)])
    assert rc == 1
    payload = json.loads(capsys.readouterr().err)
    assert payload["ok"] is False
