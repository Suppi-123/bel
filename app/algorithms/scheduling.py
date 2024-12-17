from datetime import datetime, timedelta
import pandas as pd
from pony.orm import db_session, select  # Import necessary for database access
from app.database.models import Operation, MasterOrder  # Import your models

def schedule_operations(component_quantities: dict) -> (pd.DataFrame, datetime, float, dict):
    with db_session:
        # Fetch operations and their associated master orders from the database
        operations = select(op for op in Operation)  # Fetch all operations
        master_orders = {order.order_id: order for order in select(mo for mo in MasterOrder)}  # Fetch all master orders

        # Convert operations to a DataFrame
        df = pd.DataFrame([{
            "operation_id": op.operation_id,
            "order_id": op.order.order_id,
            "work_center": op.work_center.work_center_code,
            "operation_number": op.operation_number,
            "operation_description": op.operation_description,
            "setup_time": op.setup_time,
            "per_piece_time": op.per_piece_time,
            "jump_quantity": op.jump_quantity,
            "launched_quantity": op.order.launched_quantity if op.order else 0,  # Use launched quantity from MasterOrder
            "allowed_time": op.allowed_time,
            "actual_time": op.actual_time,
            "confirmation_number": op.confirmation_number
        } for op in operations])

    if df.empty:
        return pd.DataFrame(), datetime.now(), 0.0, {}

    # Sort and prepare for scheduling
    df_sorted = df.sort_values(by=['work_center', 'operation_number'])
    start_date = datetime.now()  # Initialize start date
    if pd.isnull(start_date):
        start_date = datetime.now()

    # Adjust start_date to the next 9 AM if it's not within shift hours
    if start_date.hour < 9 or start_date.hour >= 17:
        start_date = (start_date + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)

    schedule = []
    machine_end_times = {wc.work_center_code: start_date for wc in select(wc for wc in WorkCenter)}
    current_time = start_date
    daily_production = {}
    remaining_quantities = component_quantities.copy()

    def schedule_component(component, start_time):
        component_ops = df_sorted[df_sorted["work_center"] == component]
        unit_operations = []
        end_time = start_time  # Initialize end_time

        for _, row in component_ops.iterrows():
            # Extract operation details
            operation_id = row["operation_id"]
            per_piece_time = row["per_piece_time"]
            launched_quantity = row["launched_quantity"]  # Now using the launched_quantity from MasterOrder

            # Calculate the time per fraction of quantity
            fraction_time = per_piece_time / launched_quantity
            machine = row["work_center"]

            start_time = max(start_time, machine_end_times[machine])

            # Adjust start_time to next shift if it's outside shift hours
            if start_time.hour < 9 or start_time.hour >= 17:
                start_time = (start_time + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)

            # Process each fraction of the quantity
            for i in range(1, launched_quantity + 1):
                end_time = start_time + timedelta(minutes=fraction_time)

                # If operation ends after shift, split it
                if end_time.hour >= 17:
                    remaining_time = (end_time - start_time).total_seconds() / 60
                    today_end = start_time.replace(hour=17, minute=0, second=0, microsecond=0)
                    today_duration = (today_end - start_time).total_seconds() / 60

                    # Add operation for today
                    unit_operations.append([component, operation_id, machine, start_time, today_end])
                    machine_end_times[machine] = today_end

                    # Schedule remaining time for next day
                    next_day_start = (today_end + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
                    next_day_end = next_day_start + timedelta(minutes=remaining_time - today_duration)
                    unit_operations.append([component, operation_id, machine, next_day_start, next_day_end])
                    machine_end_times[machine] = next_day_end
                    end_time = next_day_end
                else:
                    unit_operations.append([component, operation_id, machine, start_time, end_time])
                    machine_end_times[machine] = end_time

                # Update start_time for the next fraction
                start_time = end_time

        return unit_operations, end_time

    while any(remaining_quantities.values()):
        day_start = current_time.replace(hour=9, minute=0, second=0, microsecond=0)
        day_end = current_time.replace(hour=17, minute=0, second=0, microsecond=0)

        # Loop through components and schedule operations for each
        for component, quantity in remaining_quantities.items():
            if quantity > 0:
                # Schedule component operations
                component_operations, final_end_time = schedule_component(component, current_time)
                schedule.extend(component_operations)

                # Update remaining quantity
                remaining_quantities[component] -= 1  # Reduce by 1 as each quantity is processed one at a time

        current_time = final_end_time

    return pd.DataFrame(schedule, columns=["component", "operation_id", "machine", "start_time", "end_time"]), current_time, 0.0, remaining_quantities
