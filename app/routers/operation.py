from fastapi import FastAPI, HTTPException, APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime, timedelta
from pony.orm import db_session, select, Database
from app.database.models import Operation, WorkCenterMachine, WorkCenter
import logging
import traceback

# Create the router
router = APIRouter()

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Response model for scheduling data
class SchedulingResponse(BaseModel):
    part_number: str
    operation_id: int
    operation_description: str
    machine: str  # Machine name
    start_time: datetime
    end_time: datetime
    launched_quantity: int

# Dependency to ensure database connection
def get_database_connection():
    from app.database.models import db, init_database
    try:
        if not db.provider:
            init_database()
        return db
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")

@router.get("/scheduled-operations", response_model=List[SchedulingResponse])
def get_scheduled_operations(
    db: Database = Depends(get_database_connection)
):
    """
    Endpoint to retrieve scheduling data with part no, operations, machines, start time, end time, and launched quantity.
    """
    try:
        with db_session:
            # Fetch operations with machine names through WorkCenterMachine
            operations = select(op for op in Operation)
            if not operations:
                raise HTTPException(status_code=404, detail="No operations found")

            scheduled_operations = []
            last_end_time = datetime.now()  # Track the end time of the last scheduled operation

            for op in operations:
                part_number = op.order.part_number if op.order else "N/A"
                
                # Fetch machine name via WorkCenter -> WorkCenterMachine
                machine_name = "N/A"
                if op.work_center:
                    machine = select(wcm for wcm in WorkCenterMachine if wcm.work_center == op.work_center).first()
                    if machine:
                        machine_name = machine.machine_name
                
                # Initialize current_start_time based on the last machine's end time
                current_start_time = last_end_time

                for quantity in range(1, op.total_quantity + 1):
                    # Calculate the start time and end time for each quantity sequentially
                    start_time = current_start_time
                    end_time = start_time + timedelta(minutes=op.per_piece_time)

                    # Append the scheduled operation with updated times and quantity
                    scheduled_operations.append({
                        "part_number": part_number,
                        "operation_id": op.operation_id,
                        "operation_description": op.operation_description,
                        "machine": machine_name,
                        "start_time": start_time,
                        "end_time": end_time,
                        "launched_quantity": quantity  # Each quantity gets a sequential number
                    })
                    
                    # Update the start time for the next quantity
                    current_start_time = end_time  # Start time for the next quantity is the end time of the current one

                # After finishing the current machine, update the last_end_time to the end of the last quantity
                last_end_time = current_start_time  # Set the end time of the last quantity as the start time for the next machine

            return scheduled_operations

    except Exception as e:
        logger.error(f"Error fetching scheduling data: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")



class DetailedDatabaseResponse(BaseModel):
    status: str
    total_records: Dict[str, int]
    master_orders: List[Dict]
    document_references: List[Dict]
    raw_materials: List[Dict]
    work_centers: List[Dict]
    work_center_machines: List[Dict]
    operations: List[Dict]
    delivery_schedules: List[Dict]
    production_insights: Dict

def get_database_connection():
    """
    Ensure database connection is established
    """
    from app.database.models import db, init_database
    try:
        # Initialize database connection if not already connected
        if not db.provider:
            init_database()
        return db
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")

@router.get("/comprehensive-database-insights", response_model=DetailedDatabaseResponse)
def get_comprehensive_database_insights(
    db: Database = Depends(get_database_connection)
):
    """
    Retrieve comprehensive and enriched data from all database tables with additional insights
    """
    try:
        with db_session:
            # Import models
            from app.database.models import (
                MasterOrder, 
                DocumentReference, 
                RawMaterial, 
                WorkCenter, 
                WorkCenterMachine, 
                Operation, 
                DeliverySchedule
            )

            # Fetch all records with error handling and logging
            try:
                master_orders = list(select(order for order in MasterOrder))
                document_references = list(select(doc for doc in DocumentReference))
                raw_materials = list(select(rm for rm in RawMaterial))
                work_centers = list(select(wc for wc in WorkCenter))
                work_center_machines = list(select(wcm for wcm in WorkCenterMachine))
                operations = list(select(op for op in Operation))
                delivery_schedules = list(select(ds for ds in DeliverySchedule))

                # Detailed data extraction with comprehensive information
                detailed_master_orders = [
                    {
                        "order_id": order.order_id,
                        "project_name": order.project_name,
                        "part_number": order.part_number,
                        "wbs": order.wbs,
                        "sale_order": order.sale_order,
                        "part_description": order.part_description,
                        "total_operations": order.total_operations,
                        "plant": order.plant,
                        "routing_sequence_no": order.routing_sequence_no,
                        "required_quantity": order.required_quantity,
                        "launched_quantity": order.launched_quantity,
                        "production_order_no": order.production_order_no,
                    } for order in master_orders
                ]

                detailed_document_references = [
                    {
                        "document_reference_id": doc.document_reference_id,
                        "order_id": doc.order.order_id,
                        "document_type": doc.document_type,
                        "document_number": doc.document_number,
                        "revision": doc.revision
                    } for doc in document_references
                ]

                detailed_raw_materials = [
                    {
                        "raw_material_id": rm.raw_material_id,
                        "order_id": rm.order.order_id,
                        "child_part_no": rm.child_part_no,
                        "description": rm.description,
                        "qty_per_set": rm.qty_per_set,
                        "total_qty": rm.total_qty,
                        "is_available": rm.is_available
                    } for rm in raw_materials
                ]

                detailed_work_centers = [
                    {
                        "work_center_id": wc.work_center_id,
                        "work_center_code": wc.work_center_code,
                        "description": wc.description
                    } for wc in work_centers
                ]

                detailed_work_center_machines = [
                    {
                        "machine_id": wcm.machine_id,
                        "work_center_code": wcm.work_center.work_center_code,
                        "machine_name": wcm.machine_name,
                        "status": wcm.status
                    } for wcm in work_center_machines
                ]

                detailed_operations = [
                    {
                        "operation_id": op.operation_id,
                        "order_id": op.order.order_id,
                        "work_center_code": op.work_center.work_center_code,
                        "operation_number": op.operation_number,
                        "operation_description": op.operation_description,
                        "setup_time": op.setup_time,
                        "per_piece_time": op.per_piece_time,
                        "total_quantity": op.total_quantity
                    } for op in operations
                ]

                detailed_delivery_schedules = [
                    {
                        "delivery_schedule_id": ds.delivery_schedule_id,
                        "order_id": ds.order.order_id,
                        "scheduled_delivery_date": ds.scheduled_delivery_date,
                        "delivery_status": ds.delivery_status
                    } for ds in delivery_schedules
                ]

                # Production insights
                production_insights = {
                    "total_orders": len(master_orders),
                    "total_raw_materials": len(raw_materials),
                    "total_work_centers": len(work_centers),
                    "total_operations": len(operations)
                }

                return {
                    "status": "success",
                    "total_records": {
                        "master_orders": len(master_orders),
                        "document_references": len(document_references),
                        "raw_materials": len(raw_materials),
                        "work_centers": len(work_centers),
                        "work_center_machines": len(work_center_machines),
                        "operations": len(operations),
                        "delivery_schedules": len(delivery_schedules)
                    },
                    "master_orders": detailed_master_orders,
                    "document_references": detailed_document_references,
                    "raw_materials": detailed_raw_materials,
                    "work_centers": detailed_work_centers,
                    "work_center_machines": detailed_work_center_machines,
                    "operations": detailed_operations,
                    "delivery_schedules": detailed_delivery_schedules,
                    "production_insights": production_insights
                }

            except Exception as fetch_error:
                logger.error(f"Error fetching database records: {fetch_error}")
                logger.error(traceback.format_exc())
                raise HTTPException(status_code=500, detail=f"Error fetching database records: {fetch_error}")

    except Exception as e:
        logger.error(f"Comprehensive database insights error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

# Logging configuration for detailed error tracking
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)