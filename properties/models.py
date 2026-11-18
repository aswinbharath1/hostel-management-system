
from django.db import models
from django.core.validators import MinValueValidator


class Building(models.Model):
    name = models.CharField(max_length=100, unique=True)
    address = models.TextField(blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Floor(models.Model):
    building = models.ForeignKey(
        Building,
        on_delete=models.CASCADE,
        related_name='floors'
    )
    floor_number = models.PositiveIntegerField()

    class Meta:
        unique_together = ('building', 'floor_number')
        ordering = ['floor_number']

    def __str__(self):
        return f"{self.building.name} - Floor {self.floor_number}"


class Facility(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Room(models.Model):

    class RoomType(models.TextChoices):
        INDIVIDUAL = 'INDIVIDUAL', 'Individual'
        SHARED = 'SHARED', 'Shared'
        DORMITORY = 'DORMITORY', 'Dormitory'

    floor = models.ForeignKey(
        Floor,
        on_delete=models.CASCADE,
        related_name='rooms'
    )
    room_number = models.CharField(max_length=20)
    room_type = models.CharField(
        max_length=20,
        choices=RoomType.choices
    )
    capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    
    facilities = models.ManyToManyField(
        Facility,
        blank=True,
        related_name='rooms'
    )

    class Meta:
        unique_together = ('floor', 'room_number')

    def __str__(self):
        return f"{self.room_number} - {self.get_room_type_display()}"


class Bed(models.Model):
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='beds'
    )
    bed_number = models.CharField(max_length=20)

    monthly_rent = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        unique_together = ('room', 'bed_number')

    def __str__(self):
        return f"{self.room.room_number} - {self.bed_number}"