# WSL2 + NVIDIA discrete GPU

Notes on getting a Debian 13 (trixie) WSL2 distro to talk to an
NVIDIA RTX 4090 without lighting your install on fire.

## The mental model

WSL2 is a real Linux kernel running on top of Hyper-V's lightweight
hypervisor. NVIDIA support in WSL works by:

1. The **Windows-side NVIDIA driver** installs a "WSL paravirtual
   GPU" shim.
2. The Windows side exposes the GPU to Linux as `/dev/dxg`.
3. The Linux side ships a tiny user-space stub (`libcuda.so`,
   `libnvidia-ml.so`) under `/usr/lib/wsl/lib/` that talks to the
   shim.

You do **not** install Linux NVIDIA drivers inside WSL. Doing so
overwrites the stub libs and breaks GPU access until you reinstall.

## The five checks

```bash
# 1. Is this actually WSL?
grep -i microsoft /proc/version

# 2. Is the WSL kernel recent enough to ship the GPU device?
ls -l /dev/dxg

# 3. Did the Windows-side driver register itself with WSL?
ls -l /usr/lib/wsl/lib/libcuda.so

# 4. Does the user-space CUDA stub work?
nvidia-smi

# 5. Is the GPU actually a discrete one (not the integrated)?
nvidia-smi -L
```

If checks 1, 2, 3 fail in that order, fix the prior one first.

## Common state on this host

```
/dev/dxg                                                 (kernel passthrough device)
/usr/lib/wsl/lib/libcuda.so   →  libcuda.so.1.1          (CUDA runtime)
/usr/lib/wsl/lib/libnvidia-ml.so → libnvidia-ml.so.1     (NVML, used by nvidia-smi)
/usr/lib/wsl/drivers/...                                 (kernel-mode drivers)
```

These live on a Microsoft-managed mount. Don't try to update them
with `apt`. The way to update them is to update the Windows-side
NVIDIA driver and run `wsl --update` from PowerShell.

## When `nvidia-smi` returns no devices

In rough order of likelihood:

1. **Windows driver below 535.** Update from
   <https://www.nvidia.com/Download/index.aspx> (Game Ready or
   Studio, doesn't matter for compute).
2. **WSL kernel too old.** From PowerShell:
   ```powershell
   wsl --update
   wsl --shutdown
   ```
3. **You installed Linux NVIDIA drivers inside WSL.** Recover:
   ```bash
   sudo apt-get purge 'nvidia-*' 'libnvidia-*'
   # then `wsl --shutdown` from Windows so the stub libs re-bind
   ```
4. **`.wslconfig` GPU acceleration disabled.** Check `~/.wslconfig`
   on the Windows host for `gpu=false`.

## CUDA inside the env

If a lesson wants CUDA (the optional `onnxruntime-gpu` path):

```bash
# inside the activated ROS 2 env
python -c "import onnxruntime as ort; print(ort.get_device(), ort.get_available_providers())"
```

You want to see `GPU` and `CUDAExecutionProvider`. If not,
`pip install --force-reinstall onnxruntime-gpu` after uninstalling
the CPU build:

```bash
pip uninstall -y onnxruntime
pip install onnxruntime-gpu
```

This is opt-in — the tutorial's default `onnxruntime` (CPU) is fine
for the VAD model at 16 kHz mono.

## rviz2 doesn't render

Two layers can break here:

- **WSLg not running.** Test with `xeyes` or `glxgears`. If those
  don't open, `wsl --shutdown` and reopen the shell.
- **Mesa software fallback in use.** `glxinfo | grep "OpenGL renderer"`
  — if it says `llvmpipe`, the GPU isn't being used. That can still
  work for rviz at low frame rate; if you care about performance,
  see check 4 above.

## Network: discrete card and the robot are unrelated

The 4090 is for compute. Connecting to the G1 over a real network
is a separate problem covered in [unitree_g1.md](unitree_g1.md). The
two intersect only if you decide to run a heavy perception pipeline
on the GPU and stream results to the robot — out of scope for the
tutorial as-is.
