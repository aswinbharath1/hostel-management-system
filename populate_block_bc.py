
from properties.models import Building, Floor, Room, Bed, Facility
from django.db import transaction

building_names = ["Block B", "Block C"]

amenities = {
    "wifi": Facility.objects.get(name__iexact="WiFi"),
    "ac": Facility.objects.get(name__iexact="AC"),
    "hot_water": Facility.objects.get(name__iexact="HOT WATER"),
}

floor_configs = {
    0: 1,
    1: 101,
    2: 201,
}

with transaction.atomic():

    for building_name in building_names:

        building = Building.objects.get(name__iexact=building_name)

        for floor_number, start_number in floor_configs.items():

            floor = Floor.objects.get(
                building=building,
                floor_number=floor_number
            )

            # Four individual rooms
            for i in range(4):

                room_number = (
                    f"G{i+1:02d}" if floor_number == 0
                    else str(start_number + i)
                )

                room, _ = Room.objects.get_or_create(
                    floor=floor,
                    room_number=room_number,
                    defaults={
                        "room_type": "INDIVIDUAL",
                        "capacity": 1,
                    }
                )

                room.room_type = "INDIVIDUAL"
                room.capacity = 1
                room.save()

                room.facilities.set([
                    amenities["wifi"],
                    amenities["ac"],
                    amenities["hot_water"],
                ])

                bed, _ = Bed.objects.get_or_create(
                    room=room,
                    bed_number="1",
                    defaults={"monthly_rent": 5000}
                )

                bed.monthly_rent = 5000
                bed.save()

            # Four double-sharing rooms
            for i in range(4):

                room_number = (
                    f"G{i+5:02d}" if floor_number == 0
                    else str(start_number + i + 4)
                )

                room, _ = Room.objects.get_or_create(
                    floor=floor,
                    room_number=room_number,
                    defaults={
                        "room_type": "SHARED",
                        "capacity": 2,
                    }
                )

                room.room_type = "SHARED"
                room.capacity = 2
                room.save()

                room.facilities.set([amenities["wifi"]])

                for bed_no in range(1, 3):

                    bed, _ = Bed.objects.get_or_create(
                        room=room,
                        bed_number=str(bed_no),
                        defaults={"monthly_rent": 3000}
                    )

                    bed.monthly_rent = 3000
                    bed.save()

            # Two quad-sharing rooms
            for i in range(2):

                room_number = (
                    f"G{i+9:02d}" if floor_number == 0
                    else str(start_number + i + 8)
                )

                room, _ = Room.objects.get_or_create(
                    floor=floor,
                    room_number=room_number,
                    defaults={
                        "room_type": "SHARED",
                        "capacity": 4,
                    }
                )

                room.room_type = "SHARED"
                room.capacity = 4
                room.save()

                room.facilities.clear()

                for bed_no in range(1, 5):

                    bed, _ = Bed.objects.get_or_create(
                        room=room,
                        bed_number=str(bed_no),
                        defaults={"monthly_rent": 2000}
                    )

                    bed.monthly_rent = 2000
                    bed.save()

        print(f"{building_name} populated successfully!")

print("Block B and Block C population completed!")
