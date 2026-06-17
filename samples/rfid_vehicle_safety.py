# -*- coding: utf-8 -*-
# Copyright 2023 Google LLC
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
from absl.testing import absltest


class UnitTests(absltest.TestCase):
    def test_rfid_vehicle_safety(self):
        # [START rfid_vehicle_safety]
        import google.generativeai as genai

        # In-memory store: vehicle_id -> list of occupant RFID tags
        vehicle_registry: dict[str, list[str]] = {}

        def rfid_scan_entry(vehicle_id: str, rfid_tag: str) -> str:
            """Register an occupant entering a vehicle via their RFID tag.

            Args:
                vehicle_id: Unique identifier for the vehicle (e.g., plate number).
                rfid_tag: RFID tag identifier of the person boarding.

            Returns:
                A status message with the current occupant count.
            """
            occupants = vehicle_registry.setdefault(vehicle_id, [])
            if rfid_tag not in occupants:
                occupants.append(rfid_tag)
            count = len(occupants)
            return (
                f"RFID {rfid_tag} boarded vehicle {vehicle_id}. "
                f"Current occupants: {count}."
            )

        def rfid_scan_exit(vehicle_id: str, rfid_tag: str) -> str:
            """Register an occupant exiting a vehicle via their RFID tag.

            Args:
                vehicle_id: Unique identifier for the vehicle.
                rfid_tag: RFID tag identifier of the person alighting.

            Returns:
                A status message with the remaining occupant count.
            """
            occupants = vehicle_registry.get(vehicle_id, [])
            if rfid_tag in occupants:
                occupants.remove(rfid_tag)
            count = len(occupants)
            return (
                f"RFID {rfid_tag} exited vehicle {vehicle_id}. "
                f"Remaining occupants: {count}."
            )

        def get_vehicle_occupancy(vehicle_id: str) -> str:
            """Return the current occupant count for a vehicle.

            Args:
                vehicle_id: Unique identifier for the vehicle.

            Returns:
                A summary of the current occupancy.
            """
            count = len(vehicle_registry.get(vehicle_id, []))
            return f"Vehicle {vehicle_id} currently has {count} occupant(s)."

        # Wire the RFID tool functions into the model so it can call them
        # automatically and generate contextual safety reminders.
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            tools=[rfid_scan_entry, rfid_scan_exit, get_vehicle_occupancy],
            system_instruction=(
                "You are a vehicle-safety assistant that monitors RFID events. "
                "When occupants board or alight, call the appropriate RFID tool "
                "function and then issue concise safety reminders such as "
                "seatbelt usage, maximum capacity warnings, and child-safety "
                "alerts based on the current occupancy."
            ),
        )

        chat = model.start_chat(enable_automatic_function_calling=True)

        # Simulate a boarding sequence and request safety reminders
        response = chat.send_message(
            "RFID tag TAG-001 just boarded vehicle BUS-42. "
            "RFID tag TAG-002 also boarded vehicle BUS-42. "
            "Please update the occupancy and provide safety reminders."
        )
        print(response.text)

        # Simulate an exit event
        response = chat.send_message(
            "RFID tag TAG-001 has exited vehicle BUS-42. "
            "What is the current occupancy and any reminders?"
        )
        print(response.text)
        # [END rfid_vehicle_safety]

    def test_rfid_vehicle_safety_capacity_warning(self):
        # [START rfid_vehicle_safety_capacity_warning]
        import google.generativeai as genai

        MAX_CAPACITY = 4

        vehicle_registry: dict[str, list[str]] = {}

        def rfid_scan_entry(vehicle_id: str, rfid_tag: str) -> str:
            """Register an occupant entering a vehicle.

            Args:
                vehicle_id: Unique vehicle identifier.
                rfid_tag: RFID tag of the boarding person.

            Returns:
                Status including occupant count and a capacity warning when
                the vehicle is at or above maximum capacity.
            """
            occupants = vehicle_registry.setdefault(vehicle_id, [])
            if rfid_tag not in occupants:
                occupants.append(rfid_tag)
            count = len(occupants)
            warning = (
                f" WARNING: capacity limit of {MAX_CAPACITY} reached!"
                if count >= MAX_CAPACITY
                else ""
            )
            return (
                f"RFID {rfid_tag} boarded {vehicle_id}. "
                f"Occupants: {count}/{MAX_CAPACITY}.{warning}"
            )

        def get_vehicle_occupancy(vehicle_id: str) -> str:
            """Return occupancy summary for a vehicle.

            Args:
                vehicle_id: Unique vehicle identifier.

            Returns:
                Current occupant count and capacity status.
            """
            count = len(vehicle_registry.get(vehicle_id, []))
            status = "FULL" if count >= MAX_CAPACITY else "available"
            return (
                f"Vehicle {vehicle_id}: {count}/{MAX_CAPACITY} occupants – {status}."
            )

        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            tools=[rfid_scan_entry, get_vehicle_occupancy],
            system_instruction=(
                "You are a vehicle-safety assistant. Use the RFID tools to "
                "track occupancy. Always remind occupants to fasten seatbelts. "
                "If the vehicle is at or over capacity, issue an urgent warning "
                "and advise that no additional passengers should board."
            ),
        )

        chat = model.start_chat(enable_automatic_function_calling=True)

        # Board four occupants to reach maximum capacity
        response = chat.send_message(
            "RFID tags TAG-A, TAG-B, TAG-C, and TAG-D have all boarded van VAN-7. "
            "Update the occupancy and give appropriate safety reminders."
        )
        print(response.text)
        # [END rfid_vehicle_safety_capacity_warning]


if __name__ == "__main__":
    absltest.main()
