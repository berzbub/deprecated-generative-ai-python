# -*- coding: utf-8 -*-
# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""DIY Bike Concept App

An AI-assisted application for designing and building custom motorbikes.
Features include:
  - Preview various motorbike concepts and price ranges
  - Engine options, power sources and efficiency suggestions
  - Image/photo identifier and blueprint creation with parts names
  - Parts suggestions and procurement guidance
  - Mode of purpose (racing, off-road, street, etc.)
  - Layout advice, welding/cutting techniques
  - Accessory incorporation and finishing recommendations
  - Interactive AI-assisted custom bike designer

Usage:
    python samples/diy_bike_concept.py --help
    python samples/diy_bike_concept.py preview
    python samples/diy_bike_concept.py design
    python samples/diy_bike_concept.py identify --image path/to/bike.jpg
    python samples/diy_bike_concept.py blueprint --style cafe_racer --purpose street
    python samples/diy_bike_concept.py parts --style scrambler --engine 500cc
    python samples/diy_bike_concept.py procurement --style tracker --budget 5000
    python samples/diy_bike_concept.py finishing --style chopper
"""

from __future__ import annotations

import argparse
import os
import pathlib
import sys
import textwrap

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _wrap(text: str, width: int = 88) -> str:
    """Wrap text for terminal display."""
    lines = []
    for paragraph in text.split("\n"):
        if paragraph.strip():
            lines.append(textwrap.fill(paragraph, width=width))
        else:
            lines.append("")
    return "\n".join(lines)


def _print_section(title: str, content: str) -> None:
    bar = "=" * 70
    print(f"\n{bar}")
    print(f"  {title}")
    print(bar)
    print(_wrap(content))


# ---------------------------------------------------------------------------
# Bike concept data (static reference, no API call required)
# ---------------------------------------------------------------------------

BIKE_CONCEPTS = {
    "cafe_racer": {
        "description": "Stripped-down, lightweight road bike inspired by 1960s British café culture.",
        "typical_base": "Honda CB series, Triumph Bonneville, Royal Enfield",
        "price_range_usd": "$2,000 – $8,000 (donor + build)",
        "stance": "Aggressive, forward-leaning clip-on bars, rear-set pegs",
        "typical_engine": "250cc – 650cc single or parallel twin",
        "purpose": "Street, weekend rides",
    },
    "scrambler": {
        "description": "Dual-purpose bike built for light off-road use with street manners.",
        "typical_base": "Honda CL/SL, Ducati Scrambler, Triumph Scrambler",
        "price_range_usd": "$3,000 – $10,000",
        "stance": "Upright, high exhaust, knobby tyres",
        "typical_engine": "400cc – 800cc single or twin",
        "purpose": "Street + light off-road",
    },
    "chopper": {
        "description": "Long, low American-style custom with extended front fork.",
        "typical_base": "Harley-Davidson Sportster, Honda Shadow, Yamaha Virago",
        "price_range_usd": "$4,000 – $15,000+",
        "stance": "Low seat, extended fork (rake 35°–45°), ape-hanger or drag bars",
        "typical_engine": "883cc – 1200cc V-twin",
        "purpose": "Cruising, show bike",
    },
    "tracker": {
        "description": "Flat-track-inspired build with upright ergonomics and minimalist style.",
        "typical_base": "Harley Sportster, Moto Guzzi V7, BMW R-series",
        "price_range_usd": "$3,500 – $9,000",
        "stance": "Upright, flat bars, low seat",
        "typical_engine": "500cc – 1200cc twin",
        "purpose": "Street, flat-track racing",
    },
    "bobber": {
        "description": "Minimalist chopped fenders, solo seat, low-slung look.",
        "typical_base": "Harley Sportster, Indian Scout, Royal Enfield Bullet",
        "price_range_usd": "$3,000 – $9,000",
        "stance": "Low, bobbed rear fender, solo seat",
        "typical_engine": "500cc – 1200cc single or twin",
        "purpose": "Cruising, urban rides",
    },
    "supermoto": {
        "description": "Dirt bike converted for road use with slick/semi-slick tyres.",
        "typical_base": "KTM 690 SMC, Husqvarna 701, Honda XR",
        "price_range_usd": "$2,500 – $7,500",
        "stance": "Aggressive, tall, motocross-inspired",
        "typical_engine": "400cc – 690cc single",
        "purpose": "Urban, stunt, racing",
    },
    "adventure": {
        "description": "Long-distance touring bike built for on- and off-road travel.",
        "typical_base": "BMW GS, Honda Africa Twin, KTM 790 Adventure",
        "price_range_usd": "$5,000 – $20,000+",
        "stance": "Upright, tall windscreen, large fuel tank",
        "typical_engine": "650cc – 1250cc twin or inline-4",
        "purpose": "Long-distance touring, overlanding",
    },
    "electric": {
        "description": "Zero-emission custom build around an electric powertrain.",
        "typical_base": "Zero Motorcycles, custom EV conversion of ICE donor",
        "price_range_usd": "$5,000 – $25,000",
        "stance": "Varies — same as chosen style",
        "typical_engine": "5 kW – 100 kW brushless electric motor",
        "purpose": "Eco-friendly commuting, high-performance EV racing",
    },
}

ENGINE_OPTIONS = {
    "single_cylinder": {
        "displacement": "125cc – 650cc",
        "pros": "Light, simple, easy to maintain, low cost",
        "cons": "Vibration at high RPM, less top-end power",
        "best_for": "Cafe racer, scrambler, tracker, supermoto",
    },
    "parallel_twin": {
        "displacement": "300cc – 900cc",
        "pros": "Smooth power delivery, compact, good balance",
        "cons": "More complex than single",
        "best_for": "Cafe racer, scrambler, bobber",
    },
    "v_twin": {
        "displacement": "750cc – 1800cc",
        "pros": "Classic look, strong torque, character",
        "cons": "Wide engine, heat management",
        "best_for": "Chopper, bobber, tracker, cruiser",
    },
    "inline_four": {
        "displacement": "600cc – 1300cc",
        "pros": "High revving, powerful, smooth",
        "cons": "Heavy, wide, thirsty",
        "best_for": "Superbike, café racer with sportbike donor",
    },
    "electric_motor": {
        "displacement": "N/A — 5 kW to 100 kW",
        "pros": "Instant torque, zero emissions, low maintenance",
        "cons": "Battery weight/cost, limited range vs ICE",
        "best_for": "Urban commuter, eco build, EV conversion",
    },
}

POWER_SOURCES = {
    "petrol_carbureted": "Traditional carbureted gasoline engine — cheapest to build, easiest to tune manually.",
    "petrol_fuel_injected": "Modern EFI system — better efficiency, easier cold starts, tunable via ECU.",
    "electric_lithium": "Lithium-ion or LiFePO4 battery pack — lightweight, high energy density, costly.",
    "electric_lead_acid": "Lead-acid battery — cheap and accessible but heavy and lower cycle life.",
    "hybrid": "Small ICE engine combined with electric assist — complex but extends range.",
}

# ---------------------------------------------------------------------------
# AI-powered features (require GEMINI_API_KEY)
# ---------------------------------------------------------------------------

SYSTEM_INSTRUCTION = """You are an expert custom motorcycle builder and mechanical engineer with 20+ years
of experience in designing, fabricating, and finishing custom bikes. You have deep knowledge of:
- Bike geometry, frame design, and ergonomics
- Engine types (singles, twins, inline-4, electric)
- Fabrication techniques: welding (MIG, TIG, gas), cutting (angle grinder, plasma cutter, hacksaw)
- Parts sourcing: OEM, aftermarket, custom-fabricated
- Safety regulations and roadworthy requirements
- Finishing: powder coating, paint, chrome, anodising
- Accessories: lighting, instrumentation, luggage, crash protection

Always give practical, safety-conscious advice. Include measurements, material grades, and
tool requirements where relevant. Format blueprints and parts lists in clear, structured text."""


def _get_model():
    """Return a configured GenerativeModel, or raise if API key missing."""
    import google.generativeai as genai  # noqa: PLC0415

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print(
            "\n[ERROR] GEMINI_API_KEY environment variable is not set.\n"
            "Export your Gemini API key to use AI-powered features:\n"
            "  export GEMINI_API_KEY='your-key-here'\n",
            file=sys.stderr,
        )
        sys.exit(1)
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        "gemini-1.5-flash",
        system_instruction=SYSTEM_INSTRUCTION,
    )


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_preview(args: argparse.Namespace) -> None:  # noqa: ARG001
    """List all built-in bike concepts with price ranges."""
    print("\n🏍  DIY BIKE CONCEPT PREVIEW")
    print("=" * 70)
    for style, info in BIKE_CONCEPTS.items():
        print(f"\n  [{style.upper().replace('_', ' ')}]")
        print(f"    Description : {info['description']}")
        print(f"    Typical base: {info['typical_base']}")
        print(f"    Price range : {info['price_range_usd']}")
        print(f"    Stance      : {info['stance']}")
        print(f"    Engine      : {info['typical_engine']}")
        print(f"    Purpose     : {info['purpose']}")
    print()


def cmd_engines(args: argparse.Namespace) -> None:  # noqa: ARG001
    """List engine options and power sources."""
    print("\n⚙️  ENGINE OPTIONS")
    print("=" * 70)
    for name, info in ENGINE_OPTIONS.items():
        print(f"\n  [{name.upper().replace('_', ' ')}]")
        print(f"    Displacement: {info['displacement']}")
        print(f"    Pros        : {info['pros']}")
        print(f"    Cons        : {info['cons']}")
        print(f"    Best for    : {info['best_for']}")

    print("\n\n🔋  POWER SOURCES")
    print("=" * 70)
    for source, desc in POWER_SOURCES.items():
        print(f"\n  {source.upper().replace('_', ' ')}")
        print(f"    {desc}")
    print()


def cmd_identify(args: argparse.Namespace) -> None:
    """Identify bike parts from an image and suggest component names."""
    model = _get_model()
    import google.generativeai as genai  # noqa: PLC0415
    import PIL.Image  # noqa: PLC0415

    image_path = pathlib.Path(args.image)
    if not image_path.exists():
        print(f"[ERROR] Image file not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    print(f"\n🔍  Analysing image: {image_path.name} …")
    image = PIL.Image.open(image_path)

    prompt = (
        "Look at this motorcycle or motorcycle part image. "
        "Identify every visible component, name each part, and describe its function. "
        "Then suggest any custom modifications that could be made. "
        "Format your response with: "
        "1. IDENTIFIED PARTS (numbered list with part name, location, function) "
        "2. MODIFICATION SUGGESTIONS (numbered list) "
        "3. BLUEPRINT NOTES (key measurements to record for a custom build)."
    )
    response = model.generate_content([prompt, image])
    _print_section("BIKE / PART IDENTIFICATION", response.text)


def cmd_blueprint(args: argparse.Namespace) -> None:
    """Generate a text blueprint for a custom bike build."""
    model = _get_model()

    style = args.style or "cafe_racer"
    purpose = args.purpose or "street"
    engine = args.engine or "parallel_twin"
    budget = args.budget or 5000

    prompt = f"""Create a detailed DIY build blueprint for a custom {style.replace('_', ' ')} motorcycle.

Build parameters:
- Style: {style.replace('_', ' ')}
- Intended purpose: {purpose}
- Engine type: {engine.replace('_', ' ')}
- Approximate budget: USD {budget}

Please provide:

## 1. FRAME & GEOMETRY
- Recommended frame dimensions (seat height, wheelbase, rake, trail)
- Frame material (chromoly, mild steel, aluminium) and tube diameter/wall thickness
- Where to cut, shorten, or extend the donor frame
- Welding technique recommendations (MIG vs TIG, joint types)

## 2. ENGINE & DRIVETRAIN
- Engine selection advice for this style and budget
- Gearbox, primary drive, and final drive recommendations
- Mounting modifications required

## 3. SUSPENSION
- Front fork choice (stock, shortened, inverted) with spring rate guidance
- Rear suspension (mono-shock, twin shocks) setup

## 4. BRAKES
- Front and rear brake specification
- Caliper and rotor sizing

## 5. ELECTRICAL SYSTEM
- Wiring simplification tips
- Lighting, ignition, and instrumentation requirements

## 6. PARTS LIST (top 20 parts with estimated costs)

## 7. BUILD SEQUENCE (step-by-step order of operations)

## 8. SAFETY CHECKLIST (roadworthy requirements)"""

    print(f"\n📐  Generating blueprint for {style.replace('_', ' ')} ({purpose}) …")
    response = model.generate_content(prompt)
    _print_section(f"BLUEPRINT — {style.upper().replace('_', ' ')}", response.text)


def cmd_parts(args: argparse.Namespace) -> None:
    """Get parts suggestions for a given bike style and engine."""
    model = _get_model()

    style = args.style or "scrambler"
    engine = args.engine or "500cc single"
    purpose = args.purpose or "street and light off-road"

    prompt = f"""For a DIY custom {style.replace('_', ' ')} motorcycle build:
- Engine: {engine}
- Purpose: {purpose}

Please provide:

## ESSENTIAL PARTS LIST
Categorised by system (Frame, Engine, Brakes, Suspension, Electrical, Bodywork, Exhaust).
For each part include: part name, specification, new price estimate (USD), used/OEM alternative.

## EFFICIENCY SUGGESTIONS
Tips to improve fuel efficiency or EV range for this build.

## ACCESSORY OPTIONS
Recommended accessories and where to mount them (GPS, crash bars, luggage, lighting upgrades).

## FINISHING OPTIONS
Paint, powder coat, chrome, anodising recommendations for this style."""

    print(f"\n🔧  Generating parts list for {style.replace('_', ' ')} …")
    response = model.generate_content(prompt)
    _print_section(f"PARTS & SUGGESTIONS — {style.upper().replace('_', ' ')}", response.text)


def cmd_procurement(args: argparse.Namespace) -> None:
    """Get parts procurement guidance and supplier suggestions."""
    model = _get_model()

    style = args.style or "tracker"
    budget = args.budget or 5000
    region = args.region or "USA"

    prompt = f"""I am building a custom {style.replace('_', ' ')} motorcycle.
Budget: USD {budget}
Region: {region}

Please provide practical parts procurement advice:

## WHERE TO SOURCE PARTS
- Online marketplaces (with specific site names)
- Specialist custom/aftermarket suppliers
- Salvage yards and OEM surplus dealers
- Local fabrication vs. buying ready-made

## BUDGET BREAKDOWN
Suggested allocation of USD {budget} across: donor bike, frame work, engine rebuild,
suspension, brakes, electrical, bodywork, finishing, contingency.

## COST-SAVING TIPS
Strategies to reduce build cost without compromising safety or quality.

## MUST-HAVE vs NICE-TO-HAVE
Prioritised list to help manage budget overruns."""

    print(f"\n🛒  Generating procurement guide for {style.replace('_', ' ')} …")
    response = model.generate_content(prompt)
    _print_section(f"PROCUREMENT GUIDE — {style.upper().replace('_', ' ')}", response.text)


def cmd_finishing(args: argparse.Namespace) -> None:
    """Get finishing and accessories advice for a custom bike."""
    model = _get_model()

    style = args.style or "bobber"

    prompt = f"""Provide comprehensive finishing and accessory guidance for a custom {style.replace('_', ' ')} motorcycle build.

## SURFACE PREPARATION
- Metal prep process (grinding, sandblasting, epoxy primer)
- Rust prevention treatments

## PAINT & COATING OPTIONS
- DIY rattle-can techniques vs. professional spray
- Powder coating: what to send out, what to DIY
- Chrome plating: when it's worth it
- Anodising for aluminium parts

## COLOUR SCHEMES & GRAPHICS
- Classic colour palettes for this style
- Pin-striping and vintage decal ideas

## ACCESSORIES INTEGRATION
- Lighting upgrades (LED headlight, tail light, indicators)
- Instrumentation (analogue gauges vs. digital dash)
- Crash protection (frame sliders, bar ends)
- Luggage solutions (side bags, tail pack)
- Comfort (grips, seat foam, footpegs)

## FINAL INSPECTION CHECKLIST
Pre-ride safety check and first-start procedure."""

    print(f"\n🎨  Generating finishing guide for {style.replace('_', ' ')} …")
    response = model.generate_content(prompt)
    _print_section(f"FINISHING GUIDE — {style.upper().replace('_', ' ')}", response.text)


def cmd_design(args: argparse.Namespace) -> None:  # noqa: ARG001
    """Interactive AI-assisted custom bike designer (chat session)."""
    model = _get_model()

    print("\n🏗️  DIY BIKE DESIGNER — Interactive Mode")
    print("=" * 70)
    print("Chat with your AI bike-building assistant.")
    print("Ask about any aspect of your build: design, parts, welding, finishing…")
    print("Type 'exit' or 'quit' to end the session.\n")

    chat = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": (
                    "I want to build a custom motorcycle. "
                    "Please introduce yourself and ask me a few questions "
                    "to understand my skill level, budget, purpose, and preferred style."
                ),
            },
        ]
    )

    # Kick off with the initial AI greeting
    response = chat.send_message(
        "Start by greeting me and asking the key questions needed to design my custom bike."
    )
    print(f"AI Assistant:\n{_wrap(response.text)}\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nExiting designer. Happy building! 🏍")
            break

        if user_input.lower() in {"exit", "quit", "bye", "q"}:
            print("\nExiting designer. Happy building! 🏍")
            break

        if not user_input:
            continue

        response = chat.send_message(user_input)
        print(f"\nAI Assistant:\n{_wrap(response.text)}\n")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="diy_bike_concept",
        description="🏍  DIY Bike Concept App — powered by Google Generative AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python samples/diy_bike_concept.py preview
              python samples/diy_bike_concept.py engines
              python samples/diy_bike_concept.py identify --image bike.jpg
              python samples/diy_bike_concept.py blueprint --style cafe_racer --purpose street --engine parallel_twin --budget 6000
              python samples/diy_bike_concept.py parts --style scrambler --engine "500cc single" --purpose "street and light off-road"
              python samples/diy_bike_concept.py procurement --style tracker --budget 7000 --region UK
              python samples/diy_bike_concept.py finishing --style bobber
              python samples/diy_bike_concept.py design
        """),
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    # preview
    sub.add_parser("preview", help="Show all built-in bike concept styles with price ranges")

    # engines
    sub.add_parser("engines", help="List engine options and power sources")

    # identify
    p_identify = sub.add_parser("identify", help="Identify parts from a bike photo (AI)")
    p_identify.add_argument("--image", required=True, metavar="PATH", help="Path to bike image file")

    # blueprint
    p_bp = sub.add_parser("blueprint", help="Generate a build blueprint (AI)")
    p_bp.add_argument("--style", default="cafe_racer",
                      choices=list(BIKE_CONCEPTS.keys()),
                      help="Bike style (default: cafe_racer)")
    p_bp.add_argument("--purpose", default="street", help="Intended use (default: street)")
    p_bp.add_argument("--engine", default="parallel_twin", help="Engine type (default: parallel_twin)")
    p_bp.add_argument("--budget", type=int, default=5000, help="Build budget in USD (default: 5000)")

    # parts
    p_parts = sub.add_parser("parts", help="Get parts and efficiency suggestions (AI)")
    p_parts.add_argument("--style", default="scrambler",
                         choices=list(BIKE_CONCEPTS.keys()),
                         help="Bike style (default: scrambler)")
    p_parts.add_argument("--engine", default="500cc single", help="Engine spec (default: 500cc single)")
    p_parts.add_argument("--purpose", default="street and light off-road",
                         help="Intended use (default: street and light off-road)")

    # procurement
    p_proc = sub.add_parser("procurement", help="Parts procurement and budget guide (AI)")
    p_proc.add_argument("--style", default="tracker",
                        choices=list(BIKE_CONCEPTS.keys()),
                        help="Bike style (default: tracker)")
    p_proc.add_argument("--budget", type=int, default=5000, help="Total budget USD (default: 5000)")
    p_proc.add_argument("--region", default="USA", help="Region/country for sourcing (default: USA)")

    # finishing
    p_fin = sub.add_parser("finishing", help="Finishing and accessories guide (AI)")
    p_fin.add_argument("--style", default="bobber",
                       choices=list(BIKE_CONCEPTS.keys()),
                       help="Bike style (default: bobber)")

    # design (interactive)
    sub.add_parser("design", help="Interactive AI bike designer chat")

    return parser


COMMAND_HANDLERS = {
    "preview": cmd_preview,
    "engines": cmd_engines,
    "identify": cmd_identify,
    "blueprint": cmd_blueprint,
    "parts": cmd_parts,
    "procurement": cmd_procurement,
    "finishing": cmd_finishing,
    "design": cmd_design,
}


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = COMMAND_HANDLERS[args.command]
    handler(args)


if __name__ == "__main__":
    main()
