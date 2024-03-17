import sqlite3 as sq
from datetime import datetime


async def db_start():
    db = sq.connect('okay_segway.db')
    cur = db.cursor()

    # Create Segway_Status table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS Segway_Status (
            id INTEGER PRIMARY KEY,
            status TEXT
        );
    ''')

    # Create Rental_Status table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS Rental_Status (
            id INTEGER PRIMARY KEY,
            status TEXT
        );
    ''')

    # Create Employee table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS Employee (
            employee_id INTEGER PRIMARY KEY,
            name TEXT,
            telegram_id INTEGER,
            is_admin INTEGER
        );
    ''')

    # Create Segway table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS Segway (
            segway_id INTEGER PRIMARY KEY,
            segway_name TEXT,
            rate_by_min REAL,
            status_id INTEGER REFERENCES Segway_Status(id)
        );
    ''')

    # Create Rental table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS Rental (
            rental_id INTEGER PRIMARY KEY,
            rental_name VARCHAR(50),
            start_time DATETIME,
            end_time DATETIME,
            status_id INTEGER REFERENCES Rental_Status(id),
            deposit_amount REAL,
            segway_id INTEGER REFERENCES Segway(segway_id)
        );    
    ''')

    # Create Cancellation table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS Cancellation (
            cancellation_id INTEGER PRIMARY KEY,
            rental_id INTEGER REFERENCES Rental(rental_id),
            description TEXT,
            refund_amount REAL
        );        
    ''')

    db.commit()

    return db, cur


# Get user id for giving access
async def get_all_employees():
    db, cur = await db_start()
    cur.execute('SELECT name, telegram_id, is_admin FROM Employee')
    result = cur.fetchall()
    db.close()
    return result


# Get user id for giving access
async def get_employee(telegram_id):
    db, cur = await db_start()
    cur.execute('SELECT name, employee_id, is_admin FROM Employee where telegram_id = ?', (telegram_id,))
    result = cur.fetchall()
    db.close()
    return result


# Done
# Create a new segway
async def post_employee(name, status, telegram_id):
    db, cur = await db_start()

    cur.execute('''
            INSERT INTO Employee (name, is_admin, telegram_id)
            VALUES (?, ?, ?);
            ''', (name, status, telegram_id))

    db.commit()
    db.close()


# Done
# Updating an employee status
async def update_employee(employee_name, employee_status):
    db, cur = await db_start()
    cur.execute('''
            UPDATE Employee
            SET is_admin = ?
            WHERE name = ?;
            ''', (employee_status, employee_name))
    db.commit()
    db.close()


# Done
# Delete employee by name
async def delete_employee(name):
    db, cur = await db_start()
    cur.execute('DELETE FROM Employee WHERE name = ?', (name,))
    db.commit()
    db.close()


# Done
# Create a new segway
async def post_segway(segway_name, rate_by_min):
    db, cur = await db_start()

    cur.execute('''
            INSERT INTO Segway (segway_name, rate_by_min, status_id)
            VALUES (?, ?, 1);
            ''', (segway_name, rate_by_min))

    db.commit()
    db.close()


# Done
# Updating a segway price
async def update_segway(segway_name, rate_by_min):
    db, cur = await db_start()
    cur.execute('''
            UPDATE Segway
            SET rate_by_min = ?
            WHERE segway_name = ?;
            ''', (rate_by_min, segway_name))
    db.commit()
    db.close()

# Done
# Delete segway by name
async def delete_segway(name):
    db, cur = await db_start()
    cur.execute('DELETE FROM segway WHERE segway_name = ?', (name,))
    db.commit()
    db.close()


# Done
# Get all segways that are not in the rent
async def get_free_segways():
    db, cur = await db_start()
    cur.execute('''
        SELECT segway_id, segway_name, rate_by_min
        FROM Segway
        WHERE status_id = 1;
    ''')
    segways = cur.fetchall()
    db.close()
    return segways


# Done
# Get all exist segways
async def get_segways():
    db, cur = await db_start()
    cur.execute('''
        SELECT segway_id, segway_name, rate_by_min
        FROM Segway
    ''')
    segways = cur.fetchall()
    db.close()
    return segways


# Done
# Create a rental
async def add_new_rental(rental_name, start_time, end_time, status_id, deposit_amount, segway_id):
    db, cur = await db_start()

    try:
        # Create rental
        cur.execute('''
            INSERT INTO Rental (rental_name, start_time, end_time, status_id, deposit_amount, segway_id)
            VALUES (?, ?, ?, ?, ?, ?);
        ''', (rental_name, start_time, end_time, status_id, deposit_amount, segway_id))

        # Update Segway status to 'Активный' (Assuming status_id for 'Активный' is 2)
        cur.execute('''
            UPDATE Segway
            SET status_id = 2
            WHERE segway_id = ?;
        ''', (segway_id,))

        db.commit()

    except Exception as e:
        # Handle exceptions appropriately
        print(f"Error adding rental: {e}")

    finally:
        db.close()


# Get segway price
async def get_segway_price(segway_name):
    db, cur = await db_start()
    cur.execute('SELECT rate_by_min FROM Segway '
                'WHERE segway_id = (SELECT segway_id FROM Segway WHERE segway_name = ?);', (segway_name,))
    result = cur.fetchone()
    db.close()

    return result


# Get segway price by id
async def get_segway_price_id(segway_id):
    db, cur = await db_start()
    cur.execute('SELECT rate_by_min FROM Segway '
                'WHERE segway_id = ?;', (segway_id,))
    result = cur.fetchone()
    db.close()

    return result


async def get_segway_id(segway_name):
    db, cur = await db_start()
    cur.execute("SELECT segway_id FROM Segway WHERE segway_name = ?", (segway_name,))
    segways = cur.fetchall()
    db.close()
    return segways


# In Process
async def get_active_rentals():
    db, cur = await db_start()
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')

    print(today_start)  # Для отладки
    cur.execute('''
        SELECT
            Rental.rental_id,
            Rental.rental_name,
            Segway.segway_name AS Segway_Name,
            Rental.start_time,
            Rental.end_time,
            Rental_Status.status AS Rental_Status,
            Rental.deposit_amount
        FROM Rental
        JOIN Segway ON Rental.segway_id = Segway.segway_id
        JOIN Rental_Status ON Rental.status_id = Rental_Status.id
        WHERE Rental.start_time >= ? AND Rental_Status.status = 'Активный'
    ''', (today_start,))

    rentals = cur.fetchall()
    db.close()
    return rentals


# Done
# Finish active rent
async def finish_rental_request(rental_id):
    db, cur = await db_start()

    cur.execute('''
        UPDATE Rental
        SET status_id = (SELECT id FROM Rental_Status WHERE status = 'Завершен')
        WHERE rental_id = ?;
    ''', (rental_id,))

    cur.execute('''
        UPDATE Segway
        SET status_id = 1
        WHERE segway_id = (
            SELECT segway_id
            FROM Rental
            WHERE rental_id = ?
            );
    ''', (rental_id,))

    db.commit()
    db.close()


# Done
# Finish active rent
async def finish_rental_recalculate_request(rental_id, unused_time_cost):
    db, cur = await db_start()

    cur.execute('''
        UPDATE Rental
        SET status_id = (SELECT id FROM Rental_Status WHERE status = 'Завершен'),
        deposit_amount = ?
        WHERE rental_id = ?;
    ''', (unused_time_cost, rental_id))

    cur.execute('''
        UPDATE Segway
        SET status_id = 1
        WHERE segway_id = (
            SELECT segway_id
            FROM Rental
            WHERE rental_id = ?
            );
    ''', (rental_id,))

    db.commit()
    db.close()

# Done
# change segway
async def change_rental_request(rental_id, rental_name, new_end_time,
                                status_id, deposit_amount, segway_id):
    db, cur = await db_start()

    cur.execute('''
        UPDATE Rental
        SET status_id = (SELECT id FROM Rental_Status WHERE status = 'Завершен'),
        end_time = datetime('now')
        WHERE rental_id = ?;
    ''', (rental_id,))

    cur.execute('''
        UPDATE Segway
        SET status_id = 1
        WHERE segway_id = (
            SELECT segway_id
            FROM Rental
            WHERE rental_id = ?
            );
    ''', (rental_id,))

    cur.execute('''
        INSERT INTO Rental (rental_name, start_time, end_time, status_id, deposit_amount, segway_id)
        VALUES (?, datetime('now'), ?, ?, ?, ?);
    ''', (rental_name, new_end_time, status_id, deposit_amount, segway_id))

    # Update Segway status to 'Активный' (Assuming status_id for 'Активный' is 2)
    cur.execute('''
        UPDATE Segway
        SET status_id = 2
        WHERE segway_id = ?;
    ''', (segway_id,))

    db.commit()
    db.close()


# !!!!!!!!!!!
async def get_total_amount_by_employee():
    db, cur = await db_start()
    cur.execute('''
        SELECT SUM(Rental.deposit_amount) AS Total_Sum
        FROM Rental
        WHERE DATE(Rental.start_time) = CURRENT_DATE
    ''')

    total_amount = cur.fetchall()[0]
    print(total_amount)
    db.close()
    return total_amount


# Done
# Extending a rent
async def post_extension_rental(rental_id, extended_end_time_str, new_amount):
    db, cur = await db_start()

    try:
        cur.execute('''
            UPDATE Rental
            SET deposit_amount = ?,
            end_time = ?
            WHERE rental_id = ?;
        ''', (new_amount, extended_end_time_str, rental_id))

        db.commit()

    except Exception as e:
        # Handle exceptions appropriately
        print(f"Error updating rental amount: {e}")

    finally:
        db.close()


async def get_monthly_rentals():
    db, cur = await db_start()
    cur.execute('''
        SELECT 
            Rental.rental_id, 
            Rental.rental_name, 
            Rental.start_time, 
            Rental.end_time, 
            Rental.status_id, 
            Rental.deposit_amount, 
            Segway.segway_name,
            Cancellation.description AS cancellation_desc,
            Cancellation.refund_amount
        FROM Rental
        LEFT JOIN Segway ON Rental.segway_id = Segway.segway_id
        LEFT JOIN Cancellation ON Rental.rental_id = Cancellation.rental_id
        WHERE strftime('%Y-%m', Rental.start_time) = strftime('%Y-%m', CURRENT_DATE)
    ''')

    rentals = cur.fetchall()
    db.close()
    return rentals




# in process
# cancel rental
async def cancel_rental(rental_id, description):
    db, cur = await db_start()

    # Insert a new record into the Cancellation table
    cur.execute('''
            INSERT INTO Cancellation (rental_id, description, refund_amount)
            VALUES (?, ?, ?)
        ''', (rental_id, description, 0))

    # Update the Rental status to 'canceled'
    cur.execute('''
            UPDATE Rental
            SET status_id = (SELECT id FROM Rental_Status WHERE status = 'canceled')
            WHERE rental_id = ?
        ''', (rental_id,))

    cur.execute('''
        UPDATE Segway
        SET status_id = 1
        WHERE segway_id = (
            SELECT segway_id
            FROM Rental
            WHERE rental_id = ?
            );
    ''', (rental_id,))

    db.commit()
    db.close()
