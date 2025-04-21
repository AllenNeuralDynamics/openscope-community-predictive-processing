import harp
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import requests, yaml, io

def _get_yml_from_who_am_i(who_am_i: int, release: str = "main") -> io.BytesIO:
    try:
        device = _get_who_am_i_list()[who_am_i]
    except KeyError as e:
        raise KeyError(f"WhoAmI {who_am_i} not found in whoami.yml") from e

    repository_url = device.get("repositoryUrl", None)

    if repository_url is None:
        raise ValueError("Device's repositoryUrl not found in whoami.yml")
    else:  # attempt to get the device.yml from the repository
        _repo_hint_paths = [
            "{repository_url}/{release}/device.yml",
            "{repository_url}/{release}/software/bonsai/device.yml",
        ]

        yml = None
        for hint in _repo_hint_paths:
            url = hint.format(repository_url=repository_url, release=release)
            if "github.com" in url:
                url = url.replace("github.com", "raw.githubusercontent.com")
            response = requests.get(url, allow_redirects=True, timeout=5)
            if response.status_code == 200:
                yml = io.BytesIO(response.content)
                break
        if yml is None:
            raise FileNotFoundError("device.yml not found in any repository")
        else:
            return yml

def _get_who_am_i_list(url: str = "https://raw.githubusercontent.com/harp-tech/whoami/main/whoami.yml"):
    response = requests.get(url, allow_redirects=True, timeout=5)
    content = response.content.decode("utf-8")
    content = yaml.safe_load(content)
    devices = content["devices"]
    return devices


def fetch_yml(harp_path):
    with open(harp_path / 'Behavior_0.bin',mode='rb') as reg_0:
        who_am_i = int(harp.read(reg_0).values[0][0])
        yml_bytes = _get_yml_from_who_am_i(who_am_i)
    yaml_content = yml_bytes.getvalue()
    with open(harp_path / "device.yml", "wb") as f:
        f.write(yaml_content)
    return harp_path / "device.yml"


def analyze_session(harp_path):
    print(f"analyzing session at harp path {harp_path}")
    if not (harp_path / "device.yml").exists():
        print("device.yml not found, fetching from the web")
        deviceyml_path = fetch_yml(harp_path)
        print(f"device.yml made at {deviceyml_path}")

    reader = harp.create_reader(harp_path)
    print("made reader with the following registers:")
    for r in reader.registers.keys():
        print(r)

    plots_dir = harp_path / "stream_plots"
    plots_dir.mkdir(exist_ok=True)

    analogData = reader.AnalogData.read()
    analog_times = analogData.index.to_numpy()
    analog_times = analog_times - analog_times[0]
    photodiode_arr = analogData["AnalogInput0"].to_numpy()
    wheel_arr = analogData["Encoder"].to_numpy()

    fig, ax = plt.subplots()
    ax.plot(analog_times,photodiode_arr)
    fig.savefig(plots_dir / 'photodiode.png')

    fig, ax = plt.subplots()
    ax.plot(analog_times,wheel_arr)
    fig.savefig(plots_dir / 'wheel.png')

    PulseDO0 = reader.PulseDO0.read()
    print(PulseDO0)
    do0_arr = PulseDO0["PulseDO0"].to_numpy()
    do0_times = PulseDO0.index.to_numpy()
    fig, ax = plt.subplots()
    ax.plot(do0_times, do0_arr)
    fig.savefig(plots_dir / 'do0.png')

    PulseDO1 = reader.PulseDO1.read()
    print(PulseDO1)
    do1_arr = PulseDO1["PulseDO1"].to_numpy()
    do1_times = PulseDO1.index.to_numpy()
    fig, ax = plt.subplots()
    ax.plot(do1_times, do1_arr)
    fig.savefig(plots_dir / 'do1.png')


harp_path = Path(r"\\allen\aind\scratch\OpenScope\Slap2\Data\787727\20250320025428\BonsaiData\20241009_366122_Behavior.harp")
analyze_session(harp_path)