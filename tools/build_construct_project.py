#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import shutil
import struct
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "Toot-and-Tumble game"


class Ids:
    def __init__(self) -> None:
        self.uid = 1
        self.sid = 100_000_000_000_000
        self.image = 1_000_000

    def next_uid(self) -> int:
        value = self.uid
        self.uid += 1
        return value

    def next_sid(self) -> int:
        value = self.sid
        self.sid += 1_373
        return value

    def next_image(self) -> int:
        value = self.image
        self.image += 17
        return value


ids = Ids()


def rgba(hex_color: str, alpha: int = 255) -> tuple[int, int, int, int]:
    hex_color = hex_color.strip("#")
    return (
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16),
        alpha,
    )


def c3_color(hex_color: str, alpha: float = 1) -> list[float]:
    r, g, b, _ = rgba(hex_color)
    return [r / 255, g / 255, b / 255, alpha]


class Image:
    def __init__(self, width: int, height: int, fill: tuple[int, int, int, int] = (0, 0, 0, 0)) -> None:
        self.width = width
        self.height = height
        self.pixels = [fill for _ in range(width * height)]

    def set_px(self, x: int, y: int, color: tuple[int, int, int, int]) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            self.pixels[y * self.width + x] = color

    def rect(self, x: int, y: int, w: int, h: int, color: tuple[int, int, int, int]) -> None:
        for yy in range(max(0, y), min(self.height, y + h)):
            for xx in range(max(0, x), min(self.width, x + w)):
                self.set_px(xx, yy, color)

    def outline(self, x: int, y: int, w: int, h: int, color: tuple[int, int, int, int], t: int = 1) -> None:
        self.rect(x, y, w, t, color)
        self.rect(x, y + h - t, w, t, color)
        self.rect(x, y, t, h, color)
        self.rect(x + w - t, y, t, h, color)

    def circle(self, cx: int, cy: int, r: int, color: tuple[int, int, int, int]) -> None:
        rr = r * r
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) * (x - cx) + (y - cy) * (y - cy) <= rr:
                    self.set_px(x, y, color)

    def line(self, x0: int, y0: int, x1: int, y1: int, color: tuple[int, int, int, int], thickness: int = 1) -> None:
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            half = thickness // 2
            self.rect(x0 - half, y0 - half, thickness, thickness, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def save_png(self, path: Path) -> None:
        raw = bytearray()
        for y in range(self.height):
            raw.append(0)
            for x in range(self.width):
                raw.extend(self.pixels[y * self.width + x])

        def chunk(kind: bytes, data: bytes) -> bytes:
            return (
                struct.pack(">I", len(data))
                + kind
                + data
                + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
            )

        png = (
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", self.width, self.height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b"")
        )
        path.write_bytes(png)


def make_image(kind: str, width: int, height: int, base: str) -> Image:
    img = Image(width, height)
    dark = rgba("172033")
    black = rgba("1b1b1b")
    white = rgba("ffffff")

    if kind == "player_body":
        img.rect(0, 0, width, height, rgba("55d6d2", 90))
        img.outline(0, 0, width, height, rgba("124c57", 170), 2)
    elif kind == "player_art":
        img.circle(32, 17, 11, rgba("f6c28b"))
        img.rect(21, 25, 24, 27, rgba("c9363f"))
        img.rect(27, 27, 10, 23, rgba("f9f2d6"))
        img.rect(30, 33, 5, 5, rgba("ffd363"))
        img.line(21, 31, 12, 40, rgba("7d1f28"), 3)
        img.line(44, 31, 54, 25, rgba("7d1f28"), 3)
        img.rect(18, 7, 28, 6, rgba("211a30"))
        img.rect(26, 0, 16, 10, rgba("211a30"))
        img.rect(26, 9, 16, 3, rgba("d94b47"))
        img.rect(19, 51, 8, 10, rgba("2a2a2a"))
        img.rect(38, 51, 8, 10, rgba("2a2a2a"))
        img.circle(27, 15, 2, white)
        img.circle(37, 15, 2, white)
        img.circle(28, 15, 1, black)
        img.circle(38, 15, 1, black)
        img.circle(24, 21, 3, rgba("e88976"))
        img.circle(40, 21, 3, rgba("e88976"))
        img.line(27, 24, 37, 24, rgba("4c2f28"), 2)
    elif kind == "horn":
        img.rect(0, 3, width, height - 6, rgba("ffd363"))
        img.rect(0, height // 2, width, 5, rgba("c9872c"))
        img.outline(0, 5, width, height - 10, rgba("5b4311"), 2)
        img.line(8, height // 2 - 4, width - 8, height // 2 - 4, rgba("fff0a6"), 2)
    elif kind == "bell":
        img.circle(width // 2, height // 2, min(width, height) // 2 - 2, rgba("f2b33f"))
        img.circle(width // 2, height // 2, min(width, height) // 2 - 10, rgba("6f4f14"))
        img.circle(width // 2 - 5, height // 2 - 8, max(2, min(width, height) // 8), rgba("fff0a6"))
        img.outline(2, 2, width - 4, height - 4, rgba("49370f"), 2)
    elif kind == "slide":
        img.rect(0, height // 2 - 4, width, 8, rgba("f0d15a"))
        img.outline(0, height // 2 - 4, width, 8, rgba("49370f"), 1)
        img.rect(width - 10, height // 2 - 10, 8, 20, rgba("f0d15a"))
    elif kind == "wave":
        img.circle(width // 2, height // 2, min(width, height) // 2 - 2, rgba("fff6a6", 80))
        img.circle(width // 2, height // 2, min(width, height) // 2 - 10, rgba("000000", 0))
    elif kind == "car":
        img.rect(4, 18, width - 8, height - 24, rgba(base))
        img.rect(34, 6, 70, 22, rgba(base))
        img.rect(10, 0, width - 20, 7, rgba("9df46d"))
        img.rect(14, 2, width - 28, 2, rgba("f9f2d6"))
        img.rect(45, 10, 20, 12, rgba("bde7ff"))
        img.rect(72, 10, 20, 12, rgba("bde7ff"))
        img.circle(30, height - 10, 9, dark)
        img.circle(width - 30, height - 10, 9, dark)
        img.outline(4, 18, width - 8, height - 24, black, 2)
    elif kind == "bus":
        img.rect(4, 8, width - 8, height - 16, rgba("f3c747"))
        img.rect(10, 0, width - 20, 7, rgba("9df46d"))
        img.rect(14, 2, width - 28, 2, rgba("f9f2d6"))
        for x in range(22, width - 42, 34):
            img.rect(x, 15, 23, 18, rgba("bde7ff"))
        img.circle(36, height - 12, 11, dark)
        img.circle(width - 40, height - 12, 11, dark)
        img.outline(4, 8, width - 8, height - 16, black, 2)
    elif kind == "scaffold":
        img.rect(0, 0, width, 8, rgba("9fb0c7"))
        img.rect(0, height - 8, width, 8, rgba("9fb0c7"))
        img.rect(4, 0, width - 8, 7, rgba("68e7ff"))
        for x in range(0, width, 28):
            img.line(x, 0, min(width - 1, x + 28), height - 1, rgba("647187"), 2)
        for x in range(16, width - 12, 42):
            img.line(x - 8, 14, x, 8, rgba("68e7ff", 200), 2)
            img.line(x + 8, 14, x, 8, rgba("68e7ff", 200), 2)
        img.outline(0, 0, width, height, rgba("3e4858"), 2)
    elif kind == "ledge":
        img.rect(0, 0, width, height, rgba("7d8ca1"))
        img.rect(0, 0, width, 8, rgba("68e7ff"))
        img.rect(0, 8, width, 4, rgba("ced6e4"))
        img.outline(0, 0, width, height, rgba("394556"), 2)
    elif kind == "ground":
        img.rect(0, 0, width, height, rgba("777b83"))
        img.rect(0, 0, width, 12, rgba("d6d8dc"))
        img.rect(0, 0, width, 3, rgba("9df46d"))
        for x in range(0, width, 32):
            img.line(x, 0, x + 20, 12, rgba("aeb3ba"), 1)
    elif kind == "hazard":
        img.rect(0, 0, width, height, rgba(base, 190))
        img.outline(0, 0, width, height, rgba("7b1f22", 220), 2)
        for x in range(-height, width, 18):
            img.line(x, height - 1, x + height, 0, rgba("ffd166", 240), 4)
    elif kind == "dog":
        img.outline(2, 8, width - 4, height - 12, rgba("ff4747", 190), 2)
        img.rect(10, 24, 36, 18, rgba("7b4b2a"))
        img.circle(48, 25, 9, rgba("7b4b2a"))
        img.rect(14, 40, 6, 12, rgba("3f2414"))
        img.rect(36, 40, 6, 12, rgba("3f2414"))
        img.line(9, 27, 0, 18, rgba("7b4b2a"), 4)
        img.circle(51, 24, 2, black)
    elif kind == "pedestrian":
        img.outline(3, 4, width - 6, height - 6, rgba("ff4747", 190), 2)
        img.circle(width // 2, 11, 8, rgba("e7b887"))
        img.rect(width // 2 - 8, 20, 16, 27, rgba(base))
        img.line(width // 2 - 3, 47, width // 2 - 14, height - 2, dark, 4)
        img.line(width // 2 + 3, 47, width // 2 + 14, height - 2, dark, 4)
        img.line(width // 2 - 8, 27, 5, 40, rgba("e7b887"), 4)
        img.line(width // 2 + 8, 27, width - 5, 36, rgba("e7b887"), 4)
    elif kind == "flag":
        img.rect(7, 0, 6, height, rgba("e8e3d8"))
        img.rect(13, 4, width - 18, 28, rgba("f24b4b"))
        img.outline(13, 4, width - 18, 28, rgba("7b1f22"), 1)
    elif kind == "ui":
        img.rect(0, 0, width, height, rgba(base))
    elif kind == "building":
        img.rect(0, 0, width, height, rgba(base))
        for y in range(12, height - 14, 28):
            for x in range(12, width - 16, 28):
                img.rect(x, y, 12, 12, rgba("f8e7a2", 180))
        img.outline(0, 0, width, height, rgba("2f3744"), 2)
    else:
        img.rect(0, 0, width, height, rgba(base))
        img.outline(0, 0, width, height, black, 1)
    return img


ASSETS = {
    "PlayerBody": ("player_body", 36, 54, "55d6d2"),
    "PlayerArt": ("player_art", 64, 64, "ffffff"),
    "TrombonePivot": ("ui", 8, 8, "ffffff"),
    "TromboneHorn": ("horn", 160, 24, "e7bd38"),
    "TromboneBell": ("bell", 48, 48, "e7bd38"),
    "TromboneSlide": ("slide", 96, 30, "f0d15a"),
    "SoundWave": ("wave", 80, 80, "fff6a6"),
    "Ground": ("ground", 128, 64, "777b83"),
    "Car": ("car", 180, 60, "e85050"),
    "Bus": ("bus", 320, 80, "f3c747"),
    "ScaffoldPlatform": ("scaffold", 240, 28, "9fb0c7"),
    "BuildingLedge": ("ledge", 220, 32, "7d8ca1"),
    "PitHazard": ("hazard", 160, 80, "d84343"),
    "DogHazard": ("dog", 64, 58, "7b4b2a"),
    "PedestrianHazard": ("pedestrian", 48, 72, "9c4dcc"),
    "FinishFlag": ("flag", 54, 120, "f24b4b"),
    "HUD_BreathBar": ("ui", 220, 22, "63d471"),
    "HUD_SlideMeter": ("ui", 180, 18, "f0d15a"),
    "CameraAnchor": ("ui", 12, 12, "ffffff"),
    "CityBackdrop": ("building", 160, 420, "51617c"),
}


def plugin_object(name: str, plugin_id: str, properties: dict | None = None) -> dict:
    inst = {"type": name, "properties": properties or {}, "uid": ids.next_uid(), "sid": ids.next_sid(), "tags": ""}
    return {"name": name, "plugin-id": plugin_id, "sid": ids.next_sid(), "singleglobal-inst": inst}


def sprite_object(name: str, behavior_types: list[dict] | None = None, instance_variables: list[dict] | None = None) -> dict:
    kind, width, height, _ = ASSETS[name]
    collision = [0, 0, 1, 0, 1, 1, 0, 1]
    if name == "PlayerBody":
        collision = [0.08, 0.02, 0.92, 0.02, 0.92, 0.98, 0.08, 0.98]
    frame = {
        "width": width,
        "height": height,
        "originX": 0.5,
        "originY": 0.5,
        "originalSource": "",
        "exportFormat": "lossless",
        "exportQuality": 0.8,
        "fileType": "image/png",
        "imageSpriteId": ids.next_image(),
        "collisionPoly": {"points": collision},
        "useCollisionPoly": True,
        "imagePoints": [],
        "duration": 1,
        "tag": "",
    }
    return {
        "name": name,
        "plugin-id": "Sprite",
        "sid": ids.next_sid(),
        "isGlobal": False,
        "editorNewInstanceIsReplica": True,
        "instanceVariables": instance_variables or [],
        "behaviorTypes": behavior_types or [],
        "effectTypes": [],
        "animations": {
            "items": [
                {
                    "frames": [frame],
                    "sid": ids.next_sid(),
                    "name": "Default",
                    "isLooping": False,
                    "isPingPong": False,
                    "repeatCount": 1,
                    "repeatTo": 0,
                    "speed": 0,
                }
            ],
            "subfolders": [],
        },
    }


def text_object() -> dict:
    return {
        "name": "HUD_Text",
        "plugin-id": "Text",
        "sid": ids.next_sid(),
        "isGlobal": False,
        "instanceVariables": [
            {"name": "role", "type": "string", "desc": "", "show": True, "sid": ids.next_sid()}
        ],
        "behaviorTypes": [],
        "effectTypes": [],
    }


def behavior(behavior_id: str, name: str) -> dict:
    return {"behaviorId": behavior_id, "name": name, "sid": ids.next_sid()}


def sprite_inst(
    obj_type: str,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    color: str = "ffffff",
    alpha: float = 1,
    layer_visible: bool = True,
    inst_vars: dict | None = None,
    behaviors: dict | None = None,
    angle: float = 0,
) -> dict:
    return {
        "type": obj_type,
        "properties": {"initially-visible": layer_visible},
        "uid": ids.next_uid(),
        "sid": ids.next_sid(),
        "tags": "",
        "instanceVariables": inst_vars or {},
        "behaviors": behaviors or {},
        "world": {
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "originX": 0.5,
            "originY": 0.5,
            "color": c3_color(color, alpha),
            "angle": math.radians(angle),
            "zElevation": 0,
        },
    }


def text_inst(role: str, x: float, y: float, width: float, height: float, text: str, size: int, align: str = "left") -> dict:
    return {
        "type": "HUD_Text",
        "properties": {
            "text": text,
            "enable-bbcode": True,
            "font": "Arial",
            "size": size,
            "line-height": 0,
            "bold": False,
            "italic": False,
            "color": [1, 1, 1, 1],
            "horizontal-alignment": align,
            "vertical-alignment": "top",
            "wrapping": "word",
            "text-direction": "ltr",
            "icon-set": -1,
            "initially-visible": True,
            "origin": "top-left",
            "read-aloud": False,
        },
        "uid": ids.next_uid(),
        "sid": ids.next_sid(),
        "tags": "",
        "instanceVariables": {"role": role},
        "behaviors": {},
        "world": {
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "originX": 0,
            "originY": 0,
            "color": [1, 1, 1, 1],
            "angle": 0,
            "zElevation": 0,
        },
    }


def platform_behavior() -> dict:
    return {
        "Platform": {
            "properties": {
                "max-speed": 700,
                "acceleration": 2200,
                "deceleration": 1800,
                "jump-strength": 0,
                "gravity": 1600,
                "max-fall-speed": 900,
                "double-jump": False,
                "jump-sustain": 0,
                "default-controls": False,
                "enabled": True,
            }
        }
    }


def solid_behavior() -> dict:
    return {"Solid": {"properties": {"enabled": True, "tags": ""}}}


def jumpthru_behavior() -> dict:
    return {"Jumpthru": {"properties": {"enabled": True}}}


def layer(name: str, instances: list[dict], *, transparent: bool = True, bg: str = "8cc9e8", px: float = 1, py: float = 1) -> dict:
    return {
        "name": name,
        "overriden": 0,
        "subLayers": [],
        "instances": instances,
        "sid": ids.next_sid(),
        "effectTypes": [],
        "isInitiallyVisible": True,
        "isInitiallyInteractive": True,
        "isHTMLElementsLayer": False,
        "color": [1, 1, 1, 1],
        "backgroundColor": c3_color(bg, 1),
        "isTransparent": transparent,
        "parallaxX": px,
        "parallaxY": py,
        "scaleRate": 1,
        "forceOwnTexture": False,
        "renderingMode": "2d",
        "drawOrder": "z-order",
        "useRenderCells": False,
        "blendMode": "normal",
        "zElevation": 0,
        "global": False,
    }


def rect_top(obj_type: str, center_x: float, top_y: float, width: float, height: float, **kwargs: object) -> dict:
    return sprite_inst(obj_type, center_x, top_y + height / 2, width, height, **kwargs)


GAME_SCRIPT = r'''
(() => {
	const previous = globalThis.TootAndTumbleMVP;
	if (previous && previous.destroy)
		previous.destroy();

	const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
	const lerp = (a, b, t) => a + (b - a) * t;
	const approach = (value, target, amount) => {
		if (value < target)
			return Math.min(value + amount, target);
		return Math.max(value - amount, target);
	};
	const degToRad = degrees => degrees * Math.PI / 180;

	const objects = runtime.objects;
	const player = objects.PlayerBody.getFirstInstance();
	const playerArt = objects.PlayerArt.getFirstInstance();
	const pivot = objects.TrombonePivot.getFirstInstance();
	const horn = objects.TromboneHorn.getFirstInstance();
	const bell = objects.TromboneBell.getFirstInstance();
	const slide = objects.TromboneSlide.getFirstInstance();
	const cameraAnchor = objects.CameraAnchor.getFirstInstance();
	const breathBar = objects.HUD_BreathBar.getFirstInstance();
	const slideMeter = objects.HUD_SlideMeter.getFirstInstance();
	const hudTexts = Object.fromEntries(objects.HUD_Text.getAllInstances().map(t => [t.instVars.role, t]));
	const platform = player.behaviors.Platform;

	const state = {
		GameState: "Title",
		HornAngle: 90,
		LockedHornAngle: 90,
		HornSpinSpeed: 212,
		HornSweepPhase: 0,
		HornSweepCenter: 95,
		HornSweepRange: 68,
		IsHolding: 0,
		SlidePhase: 0,
		SlideValue: 0,
		SlideOscillationSpeed: 1.25,
		MinBlastPower: 360,
		MaxBlastPower: 1080,
		Breath: 100,
		BreathMax: 100,
		BreathRecharge: 145,
		BlastCooldown: 0,
		CameraX: 640,
		CameraY: 360,
		AutoScrollSpeed: 18,
		BaseRunSpeed: 85,
		startX: 250,
		startY: 560,
		waves: [],
		pressedPointers: new Set(),
		lastFailReason: "",
	};

	const hazards = [
		...objects.PitHazard.getAllInstances(),
		...objects.DogHazard.getAllInstances(),
		...objects.PedestrianHazard.getAllInstances(),
	];
	for (const h of hazards)
		h._baseX = h.x;

	function setText(role, text) {
		const inst = hudTexts[role];
		if (inst)
			inst.text = text;
	}

	function syncGlobals() {
		const g = runtime.globalVars;
		if (!g)
			return;
		for (const key of [
			"GameState", "HornAngle", "LockedHornAngle", "HornSpinSpeed", "IsHolding",
			"SlidePhase", "SlideValue", "MinBlastPower", "MaxBlastPower", "Breath",
			"BreathMax", "BreathRecharge", "BlastCooldown", "CameraX",
			"AutoScrollSpeed", "BaseRunSpeed"
		]) {
			if (Object.prototype.hasOwnProperty.call(g, key))
				g[key] = state[key];
		}
	}

	function resetRuntimeState() {
		state.GameState = "Title";
		state.HornAngle = 90;
		state.LockedHornAngle = 90;
		state.HornSweepPhase = 0;
		state.IsHolding = 0;
		state.SlidePhase = 0;
		state.SlideValue = 0;
		state.Breath = state.BreathMax;
		state.BlastCooldown = 0;
		state.CameraX = 640;
		state.CameraY = 360;
		state.lastFailReason = "";
		state.waves.length = 0;

		player.x = state.startX;
		player.y = state.startY;
		platform.isDefaultControls = false;
		platform.jumpStrength = 0;
		platform.maxSpeed = 700;
		platform.acceleration = 2200;
		platform.deceleration = 1800;
		platform.gravity = 1600;
		platform.maxFallSpeed = 900;
		platform.vectorX = 0;
		platform.vectorY = 0;

		player.isVisible = false;
		pivot.isVisible = false;
		cameraAnchor.isVisible = false;
		runtime.layout.scrollTo(state.CameraX, state.CameraY);
		syncGlobals();
	}

	function playNote(ctx, freq, duration, type, gainValue, bend, delay = 0) {
		const now = ctx.currentTime + delay;
		const target = Math.max(45, freq + bend);
		const master = ctx.createGain();
		const filter = ctx.createBiquadFilter();
		const osc = ctx.createOscillator();
		const sub = ctx.createOscillator();
		const lfo = ctx.createOscillator();
		const lfoDepth = ctx.createGain();
		filter.type = "lowpass";
		filter.frequency.setValueAtTime(clamp(freq * 5.2, 520, 1750), now);
		filter.frequency.exponentialRampToValueAtTime(clamp(target * 4.9, 460, 1550), now + duration);
		filter.Q.setValueAtTime(2.7, now);
		osc.type = type === "triangle" ? "triangle" : "sawtooth";
		sub.type = "triangle";
		osc.frequency.setValueAtTime(freq, now);
		sub.frequency.setValueAtTime(freq * 0.5, now);
		osc.frequency.exponentialRampToValueAtTime(target, now + duration);
		sub.frequency.exponentialRampToValueAtTime(target * 0.5, now + duration);
		lfo.frequency.setValueAtTime(5.8, now);
		lfoDepth.gain.setValueAtTime(freq < 120 ? 18 : 11, now);
		lfo.connect(lfoDepth);
		lfoDepth.connect(osc.detune);
		lfoDepth.connect(sub.detune);
		master.gain.setValueAtTime(0.0001, now);
		master.gain.exponentialRampToValueAtTime(gainValue, now + 0.035);
		master.gain.setValueAtTime(gainValue * 0.82, now + Math.max(0.04, duration * 0.48));
		master.gain.exponentialRampToValueAtTime(0.001, now + duration);
		osc.connect(filter);
		sub.connect(filter);
		filter.connect(master).connect(ctx.destination);
		lfo.start(now);
		lfo.stop(now + duration + 0.04);
		osc.start(now);
		sub.start(now);
		osc.stop(now + duration + 0.04);
		sub.stop(now + duration + 0.04);
	}

	function playTone(kind) {
		const AudioContextClass = globalThis.AudioContext || globalThis.webkitAudioContext;
		if (!AudioContextClass)
			return;
		try {
			const ctx = globalThis.TootTumbleAudioContext || new AudioContextClass();
			globalThis.TootTumbleAudioContext = ctx;
			if (ctx.state === "suspended")
				ctx.resume();
			if (kind === "sad") {
				const notes = [
					{ f: 330, d: 0.18, b: -65, delay: 0 },
					{ f: 294, d: 0.20, b: -70, delay: 0.22 },
					{ f: 247, d: 0.22, b: -72, delay: 0.47 },
					{ f: 196, d: 0.62, b: -96, delay: 0.76 },
				];
				for (const note of notes) {
					playNote(ctx, note.f, note.d, "sawtooth", 0.07, note.b, note.delay);
					playNote(ctx, note.f * 0.5, note.d, "triangle", 0.035, note.b * 0.5, note.delay + 0.01);
				}
				return;
			}
			const notes = kind === "big" ? [82, 123, 164, 246] : kind === "medium" ? [165, 247, 330] : [220, 330];
			const duration = kind === "big" ? 0.46 : kind === "medium" ? 0.26 : 0.16;
			const bend = kind === "big" ? -42 : kind === "medium" ? -28 : 80;
			const gainValue = kind === "big" ? 0.11 : kind === "medium" ? 0.085 : 0.07;
			notes.forEach((note, index) => {
				playNote(ctx, note, duration, index === 0 ? "sawtooth" : "square", gainValue / (index + 1.2), bend, index * 0.012);
			});
		} catch (err) {
			console.warn("Audio unavailable", err);
		}
	}

	function startGame() {
		if (state.GameState !== "Title")
			return;
		state.GameState = "Playing";
		setText("banner", "");
		setText("hint", "SPACE / PRESS: freeze angle, release to BWAAP   R / tap fail screen: restart");
		syncGlobals();
	}

	function restartRun() {
		resetRuntimeState();
		startGame();
	}

	function startHold() {
		if (state.GameState !== "Playing" || state.IsHolding || state.BlastCooldown > 0)
			return;
		state.IsHolding = 1;
		state.LockedHornAngle = state.HornAngle;
		state.SlidePhase = 0;
		state.SlideValue = 0;
		syncGlobals();
	}

	function spawnWave() {
		const wave = objects.SoundWave.createInstance("Gameplay", bell.x, bell.y);
		wave.width = 22;
		wave.height = 22;
		wave.opacity = 0.9;
		wave.colorRgb = [1, 0.94, 0.38];
		state.waves.push({ inst: wave, age: 0 });
	}

	function blast() {
		if (state.GameState !== "Playing" || !state.IsHolding)
			return;
		state.IsHolding = 0;
		const power = state.MinBlastPower + (state.MaxBlastPower - state.MinBlastPower) * state.SlideValue;
		const cost = 14 + 32 * state.SlideValue;
		if (state.Breath >= cost) {
			state.Breath = Math.max(0, state.Breath - cost);
			const launchAngle = state.LockedHornAngle + 180;
			const impulseX = Math.cos(degToRad(launchAngle)) * power;
			const impulseY = Math.sin(degToRad(launchAngle)) * power;
			platform.vectorX = clamp(platform.vectorX + impulseX, -700, 980);
			platform.vectorY = clamp(platform.vectorY + impulseY, -1250, 1050);
			spawnWave();
			playTone(state.SlideValue > 0.75 ? "big" : state.SlideValue > 0.35 ? "medium" : "short");
		} else {
			playTone("short");
			setText("hint", "Out of breath. Touch down to breathe.");
		}
		state.BlastCooldown = 0.12;
		syncGlobals();
	}

	function fail(reason) {
		if (state.GameState !== "Playing")
			return;
		state.GameState = "Failed";
		state.lastFailReason = reason || "fall";
		state.IsHolding = 0;
		platform.vectorX = 0;
		platform.vectorY = 0;
		playTone("sad");
		setText("banner", "OOF. GOOD TONE THOUGH.\nTap or press R.");
		setText("hint", `Run failed: ${state.lastFailReason}`);
		syncGlobals();
	}

	function win() {
		if (state.GameState !== "Playing")
			return;
		state.GameState = "Won";
		state.IsHolding = 0;
		platform.vectorX = 0;
		platform.vectorY = 0;
		playTone("big");
		setText("banner", "YOU MADE IT TO THE GIG.\nTap or press R to encore.");
		setText("hint", "Nice landing. The rooftop crowd is extremely relieved.");
		syncGlobals();
	}

	function restart() {
		runtime.goToLayout(runtime.layout.name);
	}

	function updateTrombone(dt) {
		const mouthX = player.x + 13;
		const mouthY = player.y - 16;
		if (state.GameState === "Playing") {
			if (!state.IsHolding) {
				state.HornSweepPhase = (state.HornSweepPhase + degToRad(state.HornSpinSpeed) * dt) % (Math.PI * 2);
				state.HornAngle = state.HornSweepCenter + Math.sin(state.HornSweepPhase) * state.HornSweepRange;
			} else {
				state.HornAngle = state.LockedHornAngle;
				state.SlidePhase = (state.SlidePhase + state.SlideOscillationSpeed * dt) % 1;
				state.SlideValue = 1 - Math.abs(state.SlidePhase * 2 - 1);
			}
		} else {
			state.HornSweepPhase = (state.HornSweepPhase + degToRad(42) * dt) % (Math.PI * 2);
			state.HornAngle = state.HornSweepCenter + Math.sin(state.HornSweepPhase) * state.HornSweepRange;
		}
		const radians = degToRad(state.HornAngle);
		const dx = Math.cos(radians);
		const dy = Math.sin(radians);
		const hornLength = 166 + (state.IsHolding ? state.SlideValue * 108 : 18);

		pivot.x = mouthX;
		pivot.y = mouthY;
		horn.x = mouthX + dx * hornLength * 0.5;
		horn.y = mouthY + dy * hornLength * 0.5;
		horn.width = hornLength;
		horn.height = 28;
		horn.angleDegrees = state.HornAngle;
		slide.x = mouthX + dx * (88 + state.SlideValue * 54);
		slide.y = mouthY + dy * (88 + state.SlideValue * 54);
		slide.width = 90 + state.SlideValue * 105;
		slide.height = 38;
		slide.angleDegrees = state.HornAngle;
		slide.isVisible = true;
		bell.x = mouthX + dx * hornLength;
		bell.y = mouthY + dy * hornLength;
		bell.width = 74;
		bell.height = 74;
		bell.angleDegrees = state.HornAngle;
	}

	function updatePlayer(dt) {
		playerArt.x = player.x;
		playerArt.y = player.y - 8;
		playerArt.angleDegrees = clamp(platform.vectorX * 0.018, -10, 10);

		if (state.GameState !== "Playing")
			return;

		if (platform.isOnFloor && !state.IsHolding) {
			platform.vectorX = approach(platform.vectorX, state.BaseRunSpeed, 680 * dt);
			state.Breath = Math.min(state.BreathMax, state.Breath + state.BreathRecharge * dt);
		} else if (state.IsHolding && platform.isOnFloor) {
			platform.vectorX = approach(platform.vectorX, 20, 420 * dt);
		}
	}

	function updateCamera(dt) {
		if (state.GameState === "Playing") {
			state.CameraX += state.AutoScrollSpeed * dt;
			if (player.x > state.CameraX + 260)
				state.CameraX = approach(state.CameraX, player.x - 260, 320 * dt);
			state.CameraX = clamp(state.CameraX, 640, runtime.layout.width - 640);
			if (player.x < state.CameraX - 820)
				fail("left behind by the gig van");
		}
		cameraAnchor.x = state.CameraX;
		cameraAnchor.y = state.CameraY;
		runtime.layout.scrollTo(state.CameraX, state.CameraY);
	}

	function updateHazards(time) {
		for (const dog of objects.DogHazard.getAllInstances())
			dog.x = dog._baseX + Math.sin(time * 2.2) * 65;
		for (const ped of objects.PedestrianHazard.getAllInstances())
			ped.x = ped._baseX + Math.sin(time * 1.45 + ped.uid) * 42;
	}

	function updateWaves(dt) {
		for (let i = state.waves.length - 1; i >= 0; i--) {
			const wave = state.waves[i];
			wave.age += dt;
			if (wave.age >= 0.36) {
				wave.inst.destroy();
				state.waves.splice(i, 1);
				continue;
			}
			const t = wave.age / 0.36;
			wave.inst.width = 24 + t * 150;
			wave.inst.height = 24 + t * 150;
			wave.inst.opacity = 0.85 * (1 - t);
		}
	}

	function updateHud() {
		if (breathBar) {
			breathBar.width = Math.max(0, state.Breath / state.BreathMax) * 220;
			breathBar.colorRgb = state.Breath > 35 ? [0.39, 0.83, 0.44] : [0.95, 0.36, 0.28];
		}
		if (slideMeter) {
			slideMeter.width = Math.max(8, state.SlideValue * 180);
			slideMeter.opacity = state.IsHolding ? 1 : 0.35;
		}
		if (state.GameState === "Title") {
			setText("banner", "TOOT & TUMBLE\nHold to freeze. Release to BWAAP.\nPress / tap to start.");
			setText("hint", "No jump button. The trombone is the jump.");
		} else if (state.GameState === "Playing") {
			const power = Math.round(state.MinBlastPower + (state.MaxBlastPower - state.MinBlastPower) * state.SlideValue);
			setText("debug", `Horn ${Math.round(state.HornAngle)}  Slide ${state.SlideValue.toFixed(2)}  Power ${power}\nBreath ${Math.round(state.Breath)}  VX ${Math.round(platform.vectorX)}  VY ${Math.round(platform.vectorY)}`);
		} else {
			setText("debug", "");
		}
	}

	function checkLevelRules() {
		if (state.GameState !== "Playing")
			return;
		const hazard = runtime.collisions.testOverlapAny(player, hazards);
		if (hazard) {
			fail(hazard.objectType.name.replace("Hazard", "").toLowerCase());
			return;
		}
		if (player.y > 900) {
			fail("fell below the city");
			return;
		}
		const finish = objects.FinishFlag.getFirstInstance();
		if (finish && runtime.collisions.testOverlap(player, finish))
			win();
	}

	function tick() {
		const dt = Math.min(runtime.dt, 1 / 30);
		if (state.BlastCooldown > 0)
			state.BlastCooldown = Math.max(0, state.BlastCooldown - dt);
		updateHazards(runtime.gameTime || performance.now() / 1000);
		updatePlayer(dt);
		updateTrombone(dt);
		updateCamera(dt);
		updateWaves(dt);
		checkLevelRules();
		updateHud();
		syncGlobals();
	}

	function onKeyDown(e) {
		if (e.code === "KeyR") {
			restartRun();
			return;
		}
		if (e.repeat)
			return;
		if (e.code === "Space") {
			if (state.GameState === "Title")
				startGame();
			else
				startHold();
		}
	}

	function onKeyUp(e) {
		if (e.code === "Space")
			blast();
	}

	function onPointerDown(e) {
		state.pressedPointers.add(e.pointerId || 1);
		if (state.GameState === "Title")
			startGame();
		else if (state.GameState === "Failed" || state.GameState === "Won")
			restartRun();
		else
			startHold();
	}

	function onPointerUp(e) {
		state.pressedPointers.delete(e.pointerId || 1);
		blast();
	}

	function destroy() {
		runtime.removeEventListener("tick", tick);
		runtime.removeEventListener("keydown", onKeyDown);
		runtime.removeEventListener("keyup", onKeyUp);
		runtime.removeEventListener("pointerdown", onPointerDown);
		runtime.removeEventListener("pointerup", onPointerUp);
		runtime.layout.removeEventListener("beforelayoutend", destroy);
	}

	resetRuntimeState();
	updateHud();
	updateTrombone(0);
	runtime.addEventListener("tick", tick);
	runtime.addEventListener("keydown", onKeyDown);
	runtime.addEventListener("keyup", onKeyUp);
	runtime.addEventListener("pointerdown", onPointerDown);
	runtime.addEventListener("pointerup", onPointerUp);
	runtime.layout.addEventListener("beforelayoutend", destroy);

	globalThis.TootAndTumbleMVP = { destroy, state };
})();
'''.strip()


def event_var(name: str, var_type: str, initial: str) -> dict:
    return {
        "eventType": "variable",
        "name": name,
        "type": var_type,
        "initialValue": initial,
        "comment": "",
        "isStatic": False,
        "isConstant": False,
        "sid": ids.next_sid(),
    }


def make_event_sheet() -> dict:
    variables = [
        event_var("GameState", "string", "Title"),
        event_var("HornAngle", "number", "90"),
        event_var("LockedHornAngle", "number", "90"),
        event_var("HornSpinSpeed", "number", "212"),
        event_var("IsHolding", "number", "0"),
        event_var("SlidePhase", "number", "0"),
        event_var("SlideValue", "number", "0"),
        event_var("MinBlastPower", "number", "360"),
        event_var("MaxBlastPower", "number", "1080"),
        event_var("Breath", "number", "100"),
        event_var("BreathMax", "number", "100"),
        event_var("BreathRecharge", "number", "145"),
        event_var("BlastCooldown", "number", "0"),
        event_var("CameraX", "number", "640"),
        event_var("AutoScrollSpeed", "number", "18"),
        event_var("BaseRunSpeed", "number", "85"),
    ]
    groups = []
    group_names = [
        "Init",
        "Input",
        "Trombone Update",
        "Player Movement",
        "Blast",
        "Camera",
        "Level/Hazards",
        "HUD",
        "Audio",
        "Debug",
    ]
    for group_name in group_names:
        children: list[dict] = [
            {"eventType": "comment", "text": f"{group_name}: implemented by the C3 script action installed at layout start."}
        ]
        if group_name == "Init":
            children.append(
                {
                    "eventType": "block",
                    "conditions": [
                        {"id": "on-start-of-layout", "objectClass": "System", "sid": ids.next_sid()}
                    ],
                    "actions": [{"type": "script", "script": GAME_SCRIPT}],
                    "sid": ids.next_sid(),
                }
            )
        groups.append(
            {
                "eventType": "group",
                "disabled": False,
                "title": group_name,
                "description": "",
                "isActiveOnStart": True,
                "children": children,
                "sid": ids.next_sid(),
            }
        )
    return {
        "name": "ES_Game",
        "events": [
            {"eventType": "comment", "text": "Toot and Tumble MVP globals and event groups."},
            *variables,
            *groups,
        ],
        "sid": ids.next_sid(),
    }


def make_layout() -> dict:
    background_instances = [
        sprite_inst("CityBackdrop", 240, 430, 220, 420, color="6d7fa0", alpha=1),
        sprite_inst("CityBackdrop", 620, 390, 260, 500, color="4c657f", alpha=1),
        sprite_inst("CityBackdrop", 1080, 430, 220, 420, color="69728c", alpha=1),
        sprite_inst("CityBackdrop", 1680, 370, 280, 560, color="56697c", alpha=1),
        sprite_inst("CityBackdrop", 2360, 410, 240, 470, color="6c7691", alpha=1),
        sprite_inst("CityBackdrop", 3140, 360, 300, 590, color="4f5f75", alpha=1),
        sprite_inst("CityBackdrop", 3780, 330, 260, 640, color="637086", alpha=1),
        sprite_inst("CityBackdrop", 4520, 390, 320, 540, color="51617c", alpha=1),
    ]

    gameplay_instances = [
        rect_top("Ground", 450, 620, 900, 120, color="ffffff", behaviors=solid_behavior()),
        rect_top("Ground", 1475, 620, 650, 120, color="ffffff", behaviors=solid_behavior()),
        rect_top("Ground", 3000, 620, 230, 120, color="ffffff", behaviors=solid_behavior()),
        rect_top("Ground", 4525, 640, 950, 120, color="ffffff", behaviors=solid_behavior()),
        rect_top("Car", 520, 570, 180, 56, color="ffffff", behaviors=jumpthru_behavior()),
        rect_top("Bus", 1300, 550, 320, 74, color="ffffff", behaviors=jumpthru_behavior()),
        rect_top("ScaffoldPlatform", 1950, 500, 240, 28, color="ffffff", behaviors=jumpthru_behavior()),
        rect_top("ScaffoldPlatform", 2300, 440, 220, 28, color="ffffff", behaviors=jumpthru_behavior()),
        rect_top("Car", 2650, 570, 170, 54, color="ffe14f", behaviors=jumpthru_behavior()),
        rect_top("BuildingLedge", 3200, 510, 220, 32, color="ffffff", behaviors=jumpthru_behavior()),
        rect_top("BuildingLedge", 3500, 440, 200, 32, color="ffffff", behaviors=jumpthru_behavior()),
        rect_top("BuildingLedge", 3800, 370, 220, 32, color="ffffff", behaviors=jumpthru_behavior()),
        rect_top("BuildingLedge", 4300, 560, 500, 36, color="ffffff", behaviors=jumpthru_behavior()),
        rect_top("PitHazard", 1050, 720, 230, 160, color="ffffff"),
        rect_top("PitHazard", 2140, 780, 920, 150, color="ffffff"),
        rect_top("PitHazard", 3340, 780, 1160, 150, color="ffffff"),
        rect_top("DogHazard", 780, 594, 58, 44, color="ffffff"),
        rect_top("PedestrianHazard", 1650, 570, 48, 72, color="ffffff"),
        rect_top("PedestrianHazard", 3560, 404, 48, 72, color="5c8bc4"),
        rect_top("PitHazard", 2900, 580, 92, 64, color="ffffff"),
        sprite_inst("FinishFlag", 4550, 500, 54, 120, color="ffffff"),
        sprite_inst("PlayerBody", 250, 560, 36, 54, color="ffffff", alpha=0.35, behaviors=platform_behavior()),
        sprite_inst("PlayerArt", 250, 552, 64, 64, color="ffffff"),
        sprite_inst("TrombonePivot", 263, 544, 8, 8, color="ffffff", alpha=0, layer_visible=False),
        sprite_inst("TromboneHorn", 330, 544, 132, 22, color="ffffff"),
        sprite_inst("TromboneSlide", 342, 544, 72, 28, color="ffffff"),
        sprite_inst("TromboneBell", 400, 544, 48, 48, color="ffffff"),
        sprite_inst("SoundWave", -200, -200, 10, 10, color="ffffff", alpha=0),
        sprite_inst("CameraAnchor", 640, 360, 12, 12, color="ffffff", alpha=0, layer_visible=False),
    ]

    ui_instances = [
        sprite_inst("HUD_BreathBar", 140, 34, 220, 22, color="ffffff"),
        sprite_inst("HUD_SlideMeter", 140, 66, 180, 18, color="ffffff"),
        text_inst("hint", 24, 92, 760, 40, "No jump button. The trombone is the jump.", 18),
        text_inst("banner", 0, 175, 1280, 270, "TOOT & TUMBLE", 42, "center"),
        text_inst("debug", 940, 18, 320, 80, "", 14),
        text_inst("labels", 24, 23, 270, 54, "BREATH\nSLIDE", 16),
    ]

    return {
        "name": "CityBlock",
        "layers": [
            layer("Background", background_instances, transparent=False, bg="8cc9e8", px=0.35, py=0.85),
            layer("Gameplay", gameplay_instances, transparent=True, bg="8cc9e8", px=1, py=1),
            layer("UI", ui_instances, transparent=True, bg="000000", px=0, py=0),
        ],
        "sid": ids.next_sid(),
        "nonworld-instances": [],
        "effectTypes": [],
        "width": 5000,
        "height": 900,
        "unboundedScrolling": False,
        "vpX": 0.5,
        "vpY": 0.5,
        "projection": "orthographic",
        "eventSheet": "ES_Game",
    }


def make_project() -> dict:
    object_items = [
        "Audio",
        "Keyboard",
        "Mouse",
        "Touch",
        "PlayerBody",
        "PlayerArt",
        "TrombonePivot",
        "TromboneHorn",
        "TromboneBell",
        "TromboneSlide",
        "SoundWave",
        "Ground",
        "Car",
        "Bus",
        "ScaffoldPlatform",
        "BuildingLedge",
        "PitHazard",
        "DogHazard",
        "PedestrianHazard",
        "FinishFlag",
        "HUD_BreathBar",
        "HUD_SlideMeter",
        "HUD_Text",
        "CameraAnchor",
        "CityBackdrop",
    ]
    return {
        "projectFormatVersion": 1,
        "savedWithRelease": 44902,
        "name": "Toot and Tumble",
        "runtime": "c3",
        "useWorker": "auto",
        "bundleAddons": False,
        "usedAddons": [
            {"type": "plugin", "id": "Audio", "name": "Audio", "author": "Scirra", "bundled": False},
            {"type": "plugin", "id": "Keyboard", "name": "Keyboard", "author": "Scirra", "bundled": False},
            {"type": "plugin", "id": "Mouse", "name": "Mouse", "author": "Scirra", "bundled": False},
            {"type": "plugin", "id": "Touch", "name": "Touch", "author": "Scirra", "bundled": False},
            {"type": "plugin", "id": "Sprite", "name": "Sprite", "author": "Scirra", "bundled": False},
            {"type": "plugin", "id": "Text", "name": "Text", "author": "Scirra", "bundled": False},
            {"type": "behavior", "id": "Platform", "name": "Platform", "author": "Scirra", "bundled": False},
            {"type": "behavior", "id": "solid", "name": "Solid", "author": "Scirra", "bundled": False},
            {"type": "behavior", "id": "jumpthru", "name": "Jump-thru", "author": "Scirra", "bundled": False},
        ],
        "uniqueId": "tootandtumblemvp",
        "objectTypes": {"items": object_items, "subfolders": []},
        "functionsName": "Functions",
        "autosaveData": None,
        "containers": [],
        "families": {"items": [], "subfolders": []},
        "layouts": {"items": ["CityBlock"], "subfolders": []},
        "eventSheets": {"items": ["ES_Game"], "subfolders": []},
        "rootFileFolders": {
            "script": {"items": [], "subfolders": []},
            "sound": {"items": [], "subfolders": []},
            "music": {"items": [], "subfolders": []},
            "video": {"items": [], "subfolders": []},
            "font": {"items": [], "subfolders": []},
            "icon": {"items": [], "subfolders": []},
            "general": {"items": [], "subfolders": []},
        },
        "timelines": {"items": [], "subfolders": []},
        "flowcharts": {"items": [], "subfolders": []},
        "properties": {
            "description": "MVP of a one-level city platformer where a rotating trombone is the only jump.",
            "version": "0.1.0",
            "autoIncrementVersion": False,
            "author": "Adam + Codex",
            "authorEmail": "",
            "authorWebsite": "",
            "appId": "com.adam.tootandtumble",
            "pixelRounding": False,
            "zAxisScale": "regular",
            "fov": 0.7853981633974483,
            "useLoaderLayout": False,
            "fullscreenMode": "letterbox-scale",
            "fullscreenQuality": "high",
            "viewportFit": "auto",
            "backgroundColor": [0, 0, 0, 0],
            "splashColor": [1, 1, 1, 0],
            "useThemeColor": False,
            "themeColor": [1, 1, 1, 0],
            "orientations": "landscape",
            "webgpu": "auto",
            "gpuPreference": "high-performance",
            "scriptsType": "module",
            "framerateMode": "vsync",
            "sampling": "nearest",
            "downscaling": "medium",
            "renderingMode": "auto",
            "anisotropicFiltering": "auto",
            "zNear": 1,
            "zFar": 10000,
            "maxSpriteSheetSize": 2048,
            "loaderStyle": "progress",
            "preloadSounds": True,
            "cordovaiOSScheme": "app",
            "cordovaAndroidScheme": "https",
            "exportFileStructure": "folders",
            "uidAllocationMode": "increment",
        },
        "viewportWidth": 1280,
        "viewportHeight": 720,
        "firstLayout": "CityBlock",
    }


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent="\t") + "\n", encoding="utf-8")


def build() -> None:
    if PROJECT.exists():
        shutil.rmtree(PROJECT)
    for folder in ["images", "objectTypes", "eventSheets", "layouts"]:
        (PROJECT / folder).mkdir(parents=True, exist_ok=True)

    for name, (kind, width, height, base) in ASSETS.items():
        make_image(kind, width, height, base).save_png(PROJECT / "images" / f"{name.lower()}-default-000.png")

    write_json(PROJECT / "objectTypes" / "Audio.json", plugin_object("Audio", "Audio", {
        "timescale-audio": "off",
        "save-load": "all",
        "play-in-background": False,
        "latency-hint": "interactive",
        "enable-multiple-tags": True,
        "panning-model": "hrtf",
        "distance-model": "inverse",
        "listener-z-height": 600,
        "reference-distance": 600,
        "maximum-distance": 10000,
        "roll-off-factor": 1,
    }))
    write_json(PROJECT / "objectTypes" / "Keyboard.json", plugin_object("Keyboard", "Keyboard"))
    write_json(PROJECT / "objectTypes" / "Mouse.json", plugin_object("Mouse", "Mouse"))
    write_json(PROJECT / "objectTypes" / "Touch.json", plugin_object("Touch", "Touch", {"use-mouse-input": True}))

    object_behaviors = {
        "PlayerBody": [behavior("Platform", "Platform")],
        "Ground": [behavior("solid", "Solid")],
        "Car": [behavior("jumpthru", "Jumpthru")],
        "Bus": [behavior("jumpthru", "Jumpthru")],
        "ScaffoldPlatform": [behavior("jumpthru", "Jumpthru")],
        "BuildingLedge": [behavior("jumpthru", "Jumpthru")],
    }
    for name in ASSETS:
        if name in {"HUD_Text"}:
            continue
        write_json(PROJECT / "objectTypes" / f"{name}.json", sprite_object(name, object_behaviors.get(name, [])))
    write_json(PROJECT / "objectTypes" / "HUD_Text.json", text_object())

    write_json(PROJECT / "layouts" / "CityBlock.json", make_layout())
    write_json(PROJECT / "eventSheets" / "ES_Game.json", make_event_sheet())
    write_json(PROJECT / "project.c3proj", make_project())

    (PROJECT / "README.md").write_text(
        "# Toot and Tumble\n\n"
        "Construct 3 MVP folder project.\n\n"
        "Open this folder in Construct 3 with **Menu -> Project -> Open -> Project folder** and choose this directory, "
        "or zip the folder contents and rename the zip to `.c3p`.\n\n"
        "Controls:\n"
        "- Space / mouse / touch press: freeze the spinning trombone angle\n"
        "- Release: blast opposite the horn direction\n"
        "- R / tap fail or win screen: restart\n\n"
        "There is no normal jump. The trombone is the jump.\n\n"
        "Visual cue: bright green tops are safe landing surfaces, cyan dashed platforms are jump-through, "
        "and red striped/glowing objects are hazards.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    build()
