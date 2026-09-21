from celery.schedules import crontab
from redbeat import RedBeatSchedulerEntry
from workers.tasks import app


def _entry_name(schedule_id: int) -> str:
    return f"schedule:{schedule_id}"


def upsert_beat_entry(schedule) -> None:
    """
    Create or update the live RedBeat entry for a ScheduledScrape row.
    Called after any create/update so the running beat process picks up
    the change on its next tick — no restart needed.
    """
    schedule_crontab = crontab(
        minute=schedule.minute,
        hour=schedule.hour,
        day_of_week=schedule.day_of_week,
        day_of_month=schedule.day_of_month,
        month_of_year=schedule.month_of_year,
    )

    entry = RedBeatSchedulerEntry(
        name=_entry_name(schedule.id),
        task="workers.tasks.run_scheduled_scrape",
        schedule=schedule_crontab,
        args=[schedule.id],
        app=app,
    )
    entry.save()


def remove_beat_entry(schedule_id: int) -> None:
    """Remove the live entry. Safe to call even if it doesn't exist."""
    try:
        entry = RedBeatSchedulerEntry.from_key(
            f"{app.conf.redbeat_key_prefix}{_entry_name(schedule_id)}", app=app
        )
        entry.delete()
    except KeyError:
        pass  # already gone
