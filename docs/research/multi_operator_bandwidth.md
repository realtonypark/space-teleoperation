# Multi-operator teleop bandwidth and latency budgets

> First-wave research note, retained for traceability. The [second-wave evidence review](second_wave_evidence.md) corrects consequential source claims; the [current synthesis](SYNTHESIS.md) governs decisions.

Scope: video downlink budget, command uplink budget, scaling to 4 and 8 concurrent operators, and how existing space/ground programs isolate and schedule sessions over intermittent links. Numbers are measured values from the cited sources unless marked `[computed]` (arithmetic from cited inputs) or `[assumption]` (design choice, stated).

## 1. Video: glass-to-glass (G2G) latency

### 1.1 Measured whole-system G2G

| System | Path | Config | G2G | Source |
|---|---|---|---|---|
| Bachhuber et al. (TU Munich) research prototype | LAN, direct cable | VGA 240 Hz global-shutter camera, software H.264, 144 Hz display | mean 19.7 ms, max 35.7 ms (≈25 ms without OS scheduling outliers); 21.2 ms with frame skipping | [Bachhuber 2018] |
| XRoboToolkit (ZED Mini → PICO 4 Ultra) | LAN, VR headset | 1280×720 stereo, 60 fps, 1 Mbps | mean 82.0 ms (σ 6.3) | [XRoboToolkit] |
| XRoboToolkit (ZED Mini → Quest 3) | LAN | same | 94.5 ms | [XRoboToolkit] |
| Open-TeleVision (ZED Mini → Quest 3) | LAN | same (its default) | 121.5 ms | [XRoboToolkit] |
| Transitive Robotics, WebRTC from robot | local | USB webcam, VGA 30 fps, software H.264 | ~120–130 ms (≈100 ms is camera + USB) | [Transitive], [ROS Discourse] |
| same | remote via cloud relay (CA→OR) | same | 150–180 ms | [Transitive], [ROS Discourse] |
| 5G teleoperated driving testbed (Kia Soul EV) | commercial 5G | Insta360 X3, 30 fps, H.264 (FFmpeg) | mean 202 ms (σ 32), 5G RTT 47 ms | [5G-TeleDrive] |
| OBS → WebRTC-WHIP, desktop GPU encoders | Gigabit LAN | 4K60, low-latency / ultra-low-latency tuning | 83–183 ms (5–11 frames); NVIDIA RTX 5070 Ti 100–117 ms | [GPU-4K] |

### 1.2 Per-stage budget (measured components)

| Stage | Measured value | Condition | Source |
|---|---|---|---|
| Camera exposure + readout | 6.0 ms | 240 Hz global-shutter industrial camera | [Bachhuber 2018] |
| Camera + USB (webcam) | ~100 ms | Logitech C925e / RealSense D435, 30 fps | [Transitive] |
| Camera capture to display, MIPI/GMSL | ~30 ms (MIPI, 720p, local WebRTC); ~50 ms (GMSL FullHD 30) | community measurements | [ROS Discourse] |
| Encode, software H.264 | 0.88 ms (VGA), 1.08 ms complex scene | CPU, x264-class | [Bachhuber 2018] |
| Encode, Jetson AGX Xavier NVENC H.265 | ~10 ms single stream; 15 ms + ≥4 ms for second concurrent stream | 1080p30 | [Jetson-Xavier] |
| Encode, Jetson Orin NX NVENC | ~23–26 ms | 4K60, max-perf, ultrafast preset (no gain from clocks) | [Jetson-OrinNX-1], [Jetson-OrinNX-2] |
| AV1 on Jetson | no ultra-low-latency tuning exposed; observed 4-frame delay was decoder (dav1d) side | Orin NX | [Jetson-AV1] |
| Network jitter buffer, WebRTC | ~10 ms typical; playout-delay hint can be set 0–10 ms | — | [Transitive], [LiveKit] |
| Decode, software H.264 | 0.27 ms (VGA) | CPU | [Bachhuber 2018] |
| Decode, Jetson Orin NX HW | 13–18 ms after VIC clock tuning (21–25 ms before) | 4K60 | [Jetson-OrinNX-1] |
| Display refresh + processing + pixel response | 8.6 ms at 144 Hz; ~17 ms at 60 Hz | — | [Bachhuber 2018], [Transitive] |

Reading of the table: with global-shutter MIPI/GMSL cameras and hardware H.264/H.265 at ≤1080p, an on-ground-equivalent G2G of 50–90 ms is demonstrated; the 100 ms USB-webcam capture path is the single largest avoidable term. Hardware encoders add 10–25 ms per frame and serialize when several streams share one NVENC engine (Xavier: +4 ms per extra stream), which matters for multi-camera satellites. Low-delay encoder settings that the sources agree on: no B-frames, CBR with small VBV, ultrafast preset, intra-refresh instead of periodic I-frames (GDR avoids per-I-frame bit-rate spikes that inflate delay) [GDR-patent].

### 1.3 Bitrate vs. resolution/fps, and how many cameras

| Data point | Value | Source |
|---|---|---|
| Open-TeleVision / XRoboToolkit default stereo stream | 1280×720, 60 fps, 1 Mbps (works at 82–121 ms G2G) | [XRoboToolkit] |
| Open-TeleVision paper config | 480×640 per eye, 60 Hz, ZED Mini | [OpenTV] |
| ZED SDK recommended stream bitrate | HD720 side-by-side 2560×720 @60: 7 Mbps H.264 / 6 Mbps H.265; HD1080 3840×1080 @30: 12.5 / 11 Mbps | [ZED-stream] |
| Teleoperated driving over 5G | 8 Mbps per camera, 32 Mbps for 4 cameras (30 fps) | [5G-AV] |
| Mobile ALOHA data collection | 3 cameras (2 wrist + 1 top), 640×480, 50 Hz | [MobileALOHA] |
| ALOHA 2 | 4 cameras (overhead, worm's-eye, 2 wrist), 848×480 RealSense D405 | [ALOHA2] |
| DROID | 3 stereo cameras (2 exterior ZED 2 + wrist ZED Mini), recorded at 15 Hz | [DROID] |
| Minimum usable frame rate, rover exploration study | 5 fps minimum (4/5/6 fps tested) | [MinFPS] |
| Surgical teleop under emulated links (libx264, 30 fps) | success 97% at 100 Mbps/3 ms; 71% at 30 Mbps/30 ms/1.5% burst loss ("LEO" tier); 35% at 5 Mbps/150 ms/2% loss | [VISTA] |

No finding on a controlled study of bitrate alone vs. manipulation success; VISTA co-varies bandwidth, delay and loss.

Camera count for manipulation data collection is consistently 3–4 per arm (one wrist + 2–3 scene views). For the operator's live feed, one scene view plus the wrist camera is the minimum that every cited rig includes; the extra views are logged for the dataset and need not be streamed live.

### 1.4 Stereo / VR requirements

| Requirement | Value | Source |
|---|---|---|
| Motion-to-photon (head tracking) | ≤20 ms, met on-device by asynchronous time-warp; the network is not in this loop | [3GPP-XR] |
| Split-rendering pose-to-render-to-photon | typically 50–60 ms | [3GPP-XR] |
| Raster split rendering bitrate | 100 Mbit/s down, 0.5 Mbit/s up; XR conferencing 3–50 Mbit/s per user | [3GPP-XR] |
| Robot stereo teleop in practice | 1 Mbps at 720p60 stereo (XRoboToolkit / Open-TeleVision); 6–7 Mbps ZED recommendation | [XRoboToolkit], [ZED-stream] |

Implication: stereo doubles pixels but not the latency budget, and remote-rendered VR (100 Mbit/s class) is not needed; the headset renders locally and the stereo camera stream is a normal video stream.

## 2. Command uplink

Joint-setpoint streaming payload: 7 × float32 = 28 B; with 8 B timestamp + 4 B sequence = 40 B `[assumption]`. Per-packet overhead from the protocol specs:

| Transport | Overhead per packet (bytes) | Packet size (40 B payload) | 50 Hz | 100 Hz | Sources |
|---|---|---|---|---|---|
| Raw UDP/IPv4 | 20 IP + 8 UDP = 28 | 68 B | 27 kbps | 54 kbps | [RFC 768] |
| QUIC DATAGRAM (1-RTT short header, 8 B CID, 1–4 B PN, 1–3 B frame, 16 B AEAD tag) | 28 + ~27–31 | ~97 B | 39 kbps | 78 kbps | [RFC 9000], [RFC 9001], [RFC 9221] |
| WebRTC data channel (DTLS 1.2 AES-GCM: 13 hdr + 8 nonce + 16 tag; SCTP: 12 common + 16 DATA chunk) | 28 + 37 + 28 = 93 | 133 B | 53 kbps | 106 kbps | [RFC 8831], [RFC 6347], [RFC 5288], [RFC 4960] |

`[computed]` from the header sizes above; excludes ACK/SACK return traffic and any CCSDS/link-layer framing. Reference points: ALOHA and Mobile ALOHA stream leader joint states at 50 Hz [ALOHA2], [MobileALOHA]; DROID records at 15 Hz [DROID]; Open-TeleVision runs its loop at 60 Hz [OpenTV]; XRoboToolkit sends a JSON pose object at 90 Hz [XRoboToolkit]; Kontur-2 ran a 500 Hz, 2-byte-per-signal haptic loop inside a 256 kbps S-band uplink [Kontur2-paper].

FEC vs. retransmission on lossy links: RFC 8854 states implementations "SHOULD prefer using RTX or Flexible FEC retransmissions instead of FEC when the connection RTT is within the application's latency budget", and to send only as much FEC as the observed loss requires [RFC 8854]. Google's WebRTC design uses a hybrid NACK/FEC whose FEC share is conditioned on RTT: FEC overhead is reduced when RTT/2 < ~50 ms, and the target protection overhead is about 20–25% of bitrate at 5% loss [WebRTC-loss]. For a LEO direct link the one-way delay is a few ms, so NACK would be viable, but a pass-limited, fading link with burst loss argues for FEC on the command stream anyway: at 100 Hz the whole stream with 100% redundancy (send each setpoint twice) is still ≤0.2 Mbps per operator `[computed]`.

## 3. Scaling to 4 and 8 operators

Per-operator video scenarios `[assumption]`, anchored to the data points in §1.3:

| Scenario | Streams per operator | Per-operator video |
|---|---|---|
| A, lean | 2 mono (scene + wrist), 640×480–720p, 30 fps, 1 Mbps each (Open-TeleVision-class) | 2 Mbps |
| B, standard | 3 mono 720p30 at 2.5 Mbps (≈ZED HD720 per-eye rate) | 7.5 Mbps |
| C, VR stereo | 1 stereo 2560×720@60 at 6 Mbps (ZED H.265) + 2 wrist 720p30 at 2 Mbps | 10 Mbps |

Totals `[computed]`; "+FEC/hdr" applies ×1.30 (25% FEC + RTP/UDP/IP ≈4% at 1200 B packets, [WebRTC-loss], [RFC 3550]):

| Operators | Scenario | Downlink video | Downlink +FEC/hdr | Uplink, 100 Hz WebRTC DC | Uplink +100% redundancy |
|---|---|---|---|---|---|
| 4 | A | 8 Mbps | 10.4 Mbps | 0.42 Mbps | 0.85 Mbps |
| 4 | B | 30 Mbps | 39 Mbps | 0.42 Mbps | 0.85 Mbps |
| 4 | C | 40 Mbps | 52 Mbps | 0.42 Mbps | 0.85 Mbps |
| 8 | A | 16 Mbps | 20.8 Mbps | 0.85 Mbps | 1.7 Mbps |
| 8 | B | 60 Mbps | 78 Mbps | 0.85 Mbps | 1.7 Mbps |
| 8 | C | 80 Mbps | 104 Mbps | 0.85 Mbps | 1.7 Mbps |

Link capacities to compare against: Kontur-2 S-band 256 kbps up / 4 Mbps down [Kontur2-paper]; NASA smallsat state-of-the-art S-band down ≤2.2 Mbps, up ≤5 Mbps; X-band down ≤220 Mbps [NASA-SoA]; ISS Ku via TDRSS 300 Mbps return / 25 Mbps forward (2013 upgrade) [ISS-Ku-2013], 600 Mbps (2019) [ISS-600]. An S-band-class downlink supports only one lean operator; Scenario A×4 needs a ≥10 Mbps downlink; B/C×8 need X-band-class or relay capacity. Uplink is not the bottleneck: one operator at 100 Hz with every packet sent twice needs ~0.21 Mbps and fits a Kontur-2-class 256 kbps uplink; 8 operators need 1.7 Mbps and fit a 5 Mbps S-band uplink with margin.

## 4. Session isolation and scheduling over intermittent links

| Practice | What is done | Numbers | Source |
|---|---|---|---|
| ISS POIC/HOSC payload commanding | One Ku link shared by all payloads; command database partitioned per user with facility enable/disable; every command transaction logged; hazardous-command design certified; remote users command through TReK; Payload Planning System schedules activities | — | [POIC] |
| TDRSS coverage | >99% of each orbit since Guam terminal (1998); Ku antenna handover between TDRS causes loss of signal | 30–60 s LOS per handover | [TDRS-coverage], [ISS-Ku-handover] |
| Astrobee (ISS free-flyer) | One Control Station commands a robot at a time; others monitor and may take over; a HOSC relay server fans one downlink stream out to many stations; on LOS the robot holds position and records locally, resumes live video on AOS; robot time is booked with the facility | commands + video over ISS Wi-Fi + Ku | [Astrobee] |
| Kontur-2 (ISS → ground robot) | Sessions bounded by direct S-band passes over DLR Weilheim; 23 sessions in 2015 | 4–8 min per pass; link delay 20–30 ms (85 ms full control RTT); 256 kbps up / 4 Mbps down; negligible loss except shadowing blackouts | [Kontur2-DLR], [Kontur2-paper], [Kontur2-RTT] |
| Analog-1 (ISS → Earth rover, via GEO relay) | Force-feedback teleop tolerated 800 ms mean delay, outliers to 3 s, with passivity control | 0.8 s mean RTT | [Analog1] |
| Commercial ground stations | AWS: on-demand contacts booked 15 min–7 days ahead, cancel ≥15 min before, per-minute billing; NASA Near Space Network deconflicts station schedules by mission priority; commercial providers let operators book passes in advance with provider-specific windows | — | [AWS-GS], [NASA-SoA] |
| Pass geometry `[computed]`, circular orbit, zenith pass | max contact per station | 400 km: 6.2 min (10° mask) / 7.9 min (5°); 500 km: 7.4 / 9.2 min; 550 km: 7.9 / 9.8 min | orbital mechanics |

The common pattern across programs: exactly one commanding authority per robot at any instant, enforced on the ground (Astrobee, POIC command partitioning); everyone else is a read-only subscriber of a single fanned-out telemetry/video stream; the onboard system has a defined safe behaviour on LOS and resumes on AOS without ground action; and robot time is booked in advance in pass-sized slots.

## Implication for our design

Budget the operator's G2G at 60–90 ms of equipment latency (global-shutter MIPI camera, hardware H.264/H.265 with intra-refresh and no B-frames, ≤10 ms jitter buffer, 60–144 Hz display) plus link propagation, and treat the 100 ms USB-webcam capture path as disqualifying. Stream two live views per operator by default (scene + wrist, 720p30 or 640×480, ~1 Mbps each, Scenario A) and log the third/fourth dataset cameras onboard for post-pass downlink; this puts 4 operators at ~10 Mbps and 8 at ~21 Mbps downlink with FEC, which rules out an S-band-only bus and sets X-band (or a relay) as the downlink requirement, while the command uplink (≤1.7 Mbps for 8 operators at 100 Hz sent twice) fits any S-band uplink. Model the command channel in the testbed as 40 B UDP payloads at 50–100 Hz with duplicate-send redundancy rather than NACK, since a pass is 6–10 min and fading is bursty. Structure sessions the way Astrobee and POIC do: a ground-side session broker grants exactly one operator write authority per arm for a pass-sized slot, fans the arm's video to observers, and the satellite holds/retracts on its own timeout with no ground involvement.

## Sources

- [Bachhuber 2018] Bachhuber, Steinbach, Freundl, Reisslein, "On the Minimization of Glass-to-Glass and Glass-to-Algorithm Delay in Video Communication", IEEE TMM 20(1), 2018. https://faculty.engineering.asu.edu/mre/wp-content/uploads/sites/31/2020/02/DelVidComm.pdf and https://arxiv.org/pdf/1510.01134
- [XRoboToolkit] XRoboToolkit: A Cross-Platform Framework for Robot Teleoperation. https://arxiv.org/pdf/2508.00097
- [OpenTV] Open-TeleVision: Teleoperation with Immersive Active Visual Feedback. https://arxiv.org/html/2407.01512
- [Transitive] WebRTC Latency: A Breakdown. https://transitiverobotics.com/blog/webrtc-latency-breakdown/
- [ROS Discourse] Where does latency in WebRTC video streaming come from? https://discourse.openrobotics.org/t/where-does-latency-in-webrtc-video-streaming-come-from-an-analysis/54566
- [5G-TeleDrive] 5G-Enabled Teleoperated Driving: An Experimental Evaluation. https://arxiv.org/html/2503.14186
- [5G-AV] Teleoperating Autonomous Vehicles over Commercial 5G. https://arxiv.org/html/2507.20438
- [GPU-4K] Evaluation of GPU Video Encoder for Low-Latency Real-Time 4K UHD Encoding. https://arxiv.org/html/2511.18688v2
- [Jetson-Xavier] Jetson AGX H.265 encode latency (NVIDIA forum). https://forums.developer.nvidia.com/t/jetson-agx-h-265-encode-latency/291361
- [Jetson-OrinNX-1] Ultra low latency on encoding and decoding, Orin NX. https://forums.developer.nvidia.com/t/ultra-low-latency-on-encoding-and-decoding/257130
- [Jetson-OrinNX-2] How to lower latency on NVENC H265, Orin NX. https://forums.developer.nvidia.com/t/how-to-lower-latency-on-nvenc-h265/347218
- [Jetson-AV1] AV1 encoder ultra low latency, Orin NX. https://forums.developer.nvidia.com/t/av1-encoder-ultra-low-latency-still-has-delay-of-4-frames-is-there-a-low-delay-setting/286764
- [NVENC-guide] NVENC Video Encoder API Programming Guide (tuning info: low latency / ultra low latency). https://docs.nvidia.com/video-technologies/video-codec-sdk/13.0/nvenc-video-encoder-api-prog-guide/
- [GDR-patent] Distributed decoding refresh / gradual decoder refresh (bit-rate smoothing rationale). https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12069250
- [LiveKit] Playout delay hints. https://docs.livekit.io/robotics/media/performance/low-latency/playout-delay/
- [ZED-stream] Stereolabs, Local Video Streaming (recommended bitrates). https://docs.stereolabs.com/docs/video/streaming.md
- [MobileALOHA] Mobile ALOHA. https://arxiv.org/html/2401.02117
- [ALOHA2] ALOHA 2. https://arxiv.org/html/2405.02292v1
- [DROID] DROID: A Large-Scale In-The-Wild Robot Manipulation Dataset. https://arxiv.org/html/2403.12945v2
- [MinFPS] Investigation of minimum frame rate for low-latency planetary surface teleoperations. https://arxiv.org/pdf/1706.03752
- [VISTA] VISTA: A Benchmark for Real-Time Video Streaming under Network Impairments in Surgical Teleoperation. https://arxiv.org/pdf/2605.08886
- [3GPP-XR] 3GPP TR 26.928, Extended Reality (XR) in 5G (summary). https://www.nrexplained.com/tr/26928/xr25g and https://www.etsi.org/deliver/etsi_tr/126900_126999/126928/16.00.00_60/tr_126928v160000p.pdf
- [RFC 768] UDP. https://www.rfc-editor.org/rfc/rfc768
- [RFC 3550] RTP. https://www.rfc-editor.org/rfc/rfc3550
- [RFC 4960] SCTP. https://www.rfc-editor.org/rfc/rfc4960
- [RFC 5288] AES-GCM cipher suites for TLS (8 B explicit nonce, 16 B tag). https://www.rfc-editor.org/rfc/rfc5288
- [RFC 6347] DTLS 1.2. https://www.rfc-editor.org/rfc/rfc6347
- [RFC 8831] WebRTC Data Channels. https://www.rfc-editor.org/rfc/rfc8831.html
- [RFC 8854] WebRTC Forward Error Correction Requirements. https://www.rfc-editor.org/rfc/rfc8854.html
- [RFC 8627] RTP Payload Format for Flexible FEC. https://www.rfc-editor.org/rfc/rfc8627.html
- [RFC 9000] QUIC transport. https://www.rfc-editor.org/rfc/rfc9000
- [RFC 9001] Using TLS to secure QUIC. https://www.rfc-editor.org/rfc/rfc9001
- [RFC 9221] An Unreliable Datagram Extension to QUIC. https://www.rfc-editor.org/rfc/rfc9221
- [WebRTC-loss] Holmer, Shemer, Paniconi, "Handling Packet Loss in WebRTC" (Google). https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/41611.pdf
- [POIC] ISS Payload Operations Integration Center overview (NTRS). https://ntrs.nasa.gov/api/citations/20130000685/downloads/20130000685.pdf
- [TDRS-coverage] NASA, TDRS: An Era of Continuous Space Communications. https://www.nasa.gov/missions/tdrs/tdrs-an-era-of-continuous-space-communications/
- [ISS-Ku-handover] NASA PIMS, Ku Tracking and Handover Activity, 2026-01-21. https://gipoc.grc.nasa.gov/pims/pimsdocs/public/ISS%20Handbook/hb_vib_equipment_Ku_Tracking_and_Handover_Activity_2026-01-21.pdf
- [ISS-Ku-2013] ISS Daily Summary Report 2013-04-03 (Ku 300 Mbps return / 25 Mbps forward). https://www.nasa.gov/blogs/stationreport/2013/04/03/iss-daily-summary-report-04-03-13/
- [ISS-600] NASA, Data Rate Increase on the ISS (600 Mbps). https://www.nasa.gov/missions/station/data-rate-increase-on-the-international-space-station-supports-future-exploration/
- [Astrobee] Astrobee: A New Tool for ISS Operations (NTRS). https://ntrs.nasa.gov/api/citations/20180003326/downloads/20180003326.pdf
- [Kontur2-DLR] DLR, Kontur-2: Controlling robots remotely from space (2015). https://dlr.de/content/en/articles/news/2015/20150819_kontur-2-controlling-robots-remotely-from-space_14598.html
- [Kontur2-paper] Artigas et al., KONTUR-2: Force-feedback Teleoperation from the International Space Station (ICRA 2016). https://elib.dlr.de/105317/1/07487246.pdf
- [Kontur2-RTT] Force-feedback teleoperation of on-ground robots from the ISS in the frame of KONTUR-2 (85 ms RTT). https://www.researchgate.net/publication/321670042_Force-feedback_teleoperation_of_on-_ground_robots_from_the_international_space_station_in_the_frame_of_the_KONTUR-2_experiment
- [Analog1] DLR, An astronaut controls a rover on Earth (Analog-1). https://www.dlr.de/en/latest/news/2019/04/20191125_astronaut-controls-rover-on-earth
- [AWS-GS] AWS Ground Station FAQs. https://aws.amazon.com/ground-station/faqs/
- [NASA-SoA] NASA State-of-the-Art Small Spacecraft Technology, Ground Data Systems and Mission Operations. https://www.nasa.gov/smallsat-institute/sst-soa/ground-data-systems-and-mission-operations/
