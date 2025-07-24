import datetime
from django.utils import timezone

# Define your work schedule
WORK_START_TIME = datetime.time(7, 30)
LUNCH_START_TIME = datetime.time(12, 0)
LUNCH_END_TIME = datetime.time(13, 0)
WORK_END_TIME = datetime.time(16, 30)
WORKDAY_HOURS = 8.0

def calculate_work_hours(start_dt, end_dt):
    """
    Calculates the total work hours between two datetimes,
    respecting the defined work schedule and skipping weekends.
    """
    if not start_dt or not end_dt or start_dt > end_dt:
        return 0

    total_hours = 0
    current_dt = start_dt

    # Loop day by day
    while current_dt.date() <= end_dt.date():
        # Skip weekends (5 = Saturday, 6 = Sunday)
        if current_dt.weekday() >= 5:
            current_dt += datetime.timedelta(days=1)
            continue

        day_start = timezone.make_aware(datetime.datetime.combine(current_dt.date(), WORK_START_TIME))
        day_end = timezone.make_aware(datetime.datetime.combine(current_dt.date(), WORK_END_TIME))
        lunch_start = timezone.make_aware(datetime.datetime.combine(current_dt.date(), LUNCH_START_TIME))
        lunch_end = timezone.make_aware(datetime.datetime.combine(current_dt.date(), LUNCH_END_TIME))

        # Determine the effective start and end for the calculation on this day
        effective_start = max(current_dt, day_start)
        effective_end = min(end_dt, day_end)
        
        if effective_start < effective_end:
            # Calculate duration for the day
            daily_duration = effective_end - effective_start
            
            # Subtract lunch break if it falls within the task's duration
            lunch_overlap_start = max(effective_start, lunch_start)
            lunch_overlap_end = min(effective_end, lunch_end)
            
            if lunch_overlap_end > lunch_overlap_start:
                daily_duration -= (lunch_overlap_end - lunch_overlap_start)
            
            total_hours += daily_duration.total_seconds() / 3600

        # Move to the start of the next day
        current_dt = timezone.make_aware(datetime.datetime.combine(current_dt.date() + datetime.timedelta(days=1), datetime.time.min))

    return round(total_hours, 2)