"""Wire format: struct-packed little-endian command and telemetry datagrams.

One datagram = one message. Timestamps are `time.monotonic_ns()` integers taken on the
sending host; ground and sat share a machine here, so the two monotonic clocks are the
same clock. On real hardware they would not be, which is why RTT is measured only at the
ground from its own echoed `t_send` (never by differencing two hosts' clocks).

NSET = 7 setpoint slots (6 SO-100 joints + 1 spare gripper slot) as the spec fixes the
wire width at 7; the SO-100's jaw is joint index 5 and slot 6 is unused.
"""
import struct

NSET = 7
CMD_MAGIC = b"STC1"
TEL_MAGIC = b"STT1"

# flags
F_SAFETY_HOLD = 1 << 0
F_GRASPED = 1 << 1
F_SUCCESS = 1 << 2
F_DONE = 1 << 3
F_ASSIST = 1 << 4   # H11: an onboard primitive, not the operator, is driving this frame

_CMD = struct.Struct("<4sIq7fB")
_TEL = struct.Struct("<4sIqIqq21fBH")

CMD_SIZE = _CMD.size
TEL_HEAD = _TEL.size


def pack_cmd(seq, t_send, setpoints, flags=0):
    return _CMD.pack(CMD_MAGIC, seq, t_send, *setpoints, flags)


def unpack_cmd(buf):
    """-> dict, or None if the datagram is not a command (trust boundary: raw UDP)."""
    if len(buf) != _CMD.size or buf[:4] != CMD_MAGIC:
        return None
    f = _CMD.unpack(buf)
    return dict(seq=f[1], t_send=f[2], setpoints=list(f[3:10]), flags=f[10])


def pack_tel(seq, t_send, last_cmd_seq, last_cmd_t_send, t_cmd_applied, q, qd, obj, flags=0, frame=b""):
    return _TEL.pack(TEL_MAGIC, seq, t_send, last_cmd_seq, last_cmd_t_send, t_cmd_applied,
                     *q, *qd, *obj, flags, len(frame)) + frame


def unpack_tel(buf):
    if len(buf) < _TEL.size or buf[:4] != TEL_MAGIC:
        return None
    f = _TEL.unpack(buf[:_TEL.size])
    n = f[-1]
    if len(buf) != _TEL.size + n:
        return None
    return dict(seq=f[1], t_send=f[2], last_cmd_seq=f[3], last_cmd_t_send=f[4],
                t_cmd_applied=f[5], q=list(f[6:13]), qd=list(f[13:20]),
                obj=list(f[20:27]), flags=f[27], frame=buf[_TEL.size:])
