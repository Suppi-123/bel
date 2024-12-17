from pony.orm import Database, Required, Optional, PrimaryKey, Set
from datetime import date

db = Database()

class MasterOrder(db.Entity):
    order_id = PrimaryKey(int, auto=True)
    project_name = Required(str)
    part_number = Required(str)
    wbs = Required(str)
    sale_order = Required(str)
    part_description = Required(str)
    total_operations = Required(int)
    plant = Required(str)
    routing_sequence_no = Required(int)
    required_quantity = Required(int)
    launched_quantity = Required(int)
    production_order_no = Required(str)
    # Relationships
    document_references = Set('DocumentReference')
    raw_materials = Set('RawMaterial')
    operations = Set('Operation')
    delivery_schedules = Set('DeliverySchedule')

class DocumentReference(db.Entity):
    document_reference_id = PrimaryKey(int, auto=True)
    order = Required(MasterOrder)
    document_type = Required(str)  # e.g., "OARC Rev", "Drawing No", etc.
    document_number = Required(str)
    revision = Required(str, default='--')

class RawMaterial(db.Entity):
    raw_material_id = PrimaryKey(int, auto=True)
    order = Required(MasterOrder)
    sl_no = Required(str)
    child_part_no = Required(str)
    description = Required(str)
    qty_per_set = Required(float)
    uom = Required(str)
    total_qty = Required(float)
    is_available = Required(bool, default=True)

class WorkCenter(db.Entity):
    work_center_id = PrimaryKey(int, auto=True)
    work_center_code = Required(str, unique=True)
    description = Optional(str)
    machines = Set('WorkCenterMachine')
    operations = Set('Operation')

class WorkCenterMachine(db.Entity):
    machine_id = PrimaryKey(int, auto=True)
    work_center = Required(WorkCenter)
    machine_name = Required(str)
    status = Optional(str)  # e.g., "Active", "Maintenance", "Inactive"

class Operation(db.Entity):
    operation_id = PrimaryKey(int, auto=True)
    order = Required(MasterOrder)
    work_center = Required(WorkCenter)
    operation_number = Required(int)
    operation_description = Required(str)
    setup_time = Required(float)
    per_piece_time = Required(float)
    jump_quantity = Required(int)
    total_quantity = Required(int)
    allowed_time = Required(float)
    actual_time = Optional(float)
    confirmation_number = Optional(str)

class DeliverySchedule(db.Entity):
    delivery_schedule_id = PrimaryKey(int, auto=True)
    order = Required(MasterOrder)
    scheduled_delivery_date = Required(date)
    actual_delivery_date = Optional(date)
    delivery_status = Required(str)  # e.g., "Scheduled", "In Transit", "Delivered"

# Database connection setup
def init_database():
    from os import getenv
    from dotenv import load_dotenv
    
    load_dotenv()  # Load environment variables
    
    if not db.provider:
        db.bind(
            provider='postgres',
            user=getenv('DB_USER'),
            password=getenv('DB_PASSWORD'),
            host=getenv('DB_HOST'),
            database=getenv('DB_NAME'),
            port=getenv('DB_PORT')
        )
        db.generate_mapping(create_tables=True)