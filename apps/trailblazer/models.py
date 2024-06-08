from django.db import models

from apps.discord.models import DiscordAccount
from apps.overrides.models import Base


class TrailblazerTuesdayAttendance(Base):
    class Meta:
        db_table = "TrailblazerTuesdayAttendance"
        ordering = [
            "-attendance_date",
        ]
        verbose_name = "Tuesday Attendance"
        verbose_name_plural = "Tuesday Attendances"

    attendee_discord = models.ForeignKey(
        DiscordAccount,
        on_delete=models.RESTRICT,
        verbose_name="Attendee Discord",
        related_name="trailblazer_tuesday_attendees",
    )
    attendance_date = models.DateField(verbose_name="Attendance Date")

    def __str__(self):
        return f"{str(self.attendee_discord)} attended on {self.attendance_date}"
