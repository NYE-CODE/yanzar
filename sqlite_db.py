import sqlite3 as sq
from datetime import datetime

async def db_start():
    db = sq.connect('okay_segway_db.db')
    cur = db.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS Segways (
            segway_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255),
            price DECIMAL(10, 2)
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS Rentals (
            rental_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name VARCHAR(255),
            segway_id INT,
            start_date DATETIME,
            end_date DATETIME,
            status VARCHAR(255),
            amount DECIMAL(10, 2),
            extension DATETIME,
            stop DATETIME,
            amount_for_customer DECIMAL(10, 2),
            FOREIGN KEY (segway_id) REFERENCES Segways (segway_id)
        )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS SegwayChangeHistory (
        history_id INTEGER PRIMARY KEY AUTOINCREMENT,
        rental_id INT,
        segway_id INT,
        change_date DATETIME,
        old_segway INT,
        new_segway INT,
        new_price DECIMAL(10, 2),
        FOREIGN KEY (rental_id) REFERENCES Rentals (rental_id),
        FOREIGN KEY (segway_id) REFERENCES Segways (segway_id)
    )
    ''')

    db.commit()

    return db, cur


async def get_segways():
    db, cur = await db_start()
    cur.execute('SELECT name, price FROM Segways')
    segways = cur.fetchall()
    db.close()
    return segways


async def get_active_rentals():
    db, cur = await db_start()
    current_date = datetime.now().strftime('%Y-%m-%d')

    cur.execute(f'''
    SELECT r.rental_id, r.client_name, s1.name AS segway_name, r.start_date, r.end_date, r.status, r.amount, r.extension, r.stop, 
        r.amount_for_customer, c.change_date, s2.name AS old_segway_name, s3.name AS new_segway_name, c.new_price 
    FROM Rentals r
    LEFT JOIN SegwayChangeHistory c ON r.rental_id = c.rental_id
    LEFT JOIN Segways s1 ON r.segway_id = s1.segway_id
    LEFT JOIN Segways s2 ON c.old_segway = s2.segway_id
    LEFT JOIN Segways s3 ON c.new_segway = s3.segway_id
    WHERE DATE(r.start_date) = '{current_date}';
    ''')
    rentals = cur.fetchall()
    db.close()
    return rentals


async def get_today_rentals():
    db, cur = await db_start()
    current_date = datetime.now().strftime('%Y-%m-%d')

    cur.execute(f'''
    SELECT r.*, c.change_date, c.old_segway, c.new_segway, c.new_price
    FROM Rentals r
    LEFT JOIN SegwayChangeHistory c ON r.rental_id = c.rental_id
    WHERE DATE(r.start_date) = '{current_date}';
    ''')
    rentals = cur.fetchall()
    db.close()
    return rentals


async def get_total_amount():
    db, cur = await db_start()
    current_date = datetime.now().strftime('%Y-%m-%d')

    cur.execute(f'''
    SELECT SUM(amount) AS total_amount
        FROM Rentals
        WHERE DATE(end_date) = '{current_date}' AND status = 'Завершен';
    ''')
    rentals = cur.fetchall()
    db.close()
    return rentals


async def post_rentals(user_id, equipment_name, start_time, end_time, total_cost):
    db, cur = await db_start()
    try:
        cur.execute("SELECT segway_id FROM Segways WHERE name = ?", (equipment_name,))
        equipment_id = cur.fetchone()
        if equipment_id:
            equipment_id = equipment_id[0]
        else:
            print(f"Error: Equipment '{equipment_name}' not found.")
            return

        cur.execute('''
        INSERT INTO Rentals (client_name, segway_id, start_date, end_date, status, amount)
            VALUES (?, ?, ?, ?, ?, ?);
        ''', (user_id, equipment_id, start_time, end_time, 'Активная', total_cost))
        db.commit()
        print(f"Rental created: user_id={user_id}, equipment_id={equipment_id}, start_time={start_time}, end_time={end_time}, total_cost={total_cost}")
    except Exception as e:
        print("Error creating rental:", str(e))
    db.close()



async def get_equipment_price(equipment_name):
    db, cur = await db_start()
    cur.execute('SELECT price FROM segways WHERE name = ?', (equipment_name,))
    result = cur.fetchone()
    db.close()
    return result[0] if result else 0  # Возвращаем стоимость или 0, если запись не найдена


async def get_segway_price(segway_id):
    db, cur = await db_start()
    cur.execute('SELECT price FROM segways WHERE segway_id = ?', (segway_id,))
    result = cur.fetchone()
    db.close()
    return result[0] if result else 0  # Возвращаем стоимость или 0, если запись не найдена


async def post_extension_rental(rental_id, extended_end_time_str, new_amount):
    db, cur = await db_start()
    cur.execute('''
    UPDATE Rentals
    SET end_date = ?, amount = ?, extension = DATETIME('NOW')
    WHERE rental_id = ?;
    ''', (extended_end_time_str, new_amount, rental_id))
    db.commit()
    db.close()


async def finish_rental_request(rental_id):
    db, cur = await db_start()
    cur.execute('''
    UPDATE Rentals
        SET status = 'Завершен', end_date = DATETIME('NOW')
        WHERE rental_id = ?;
    ''', (rental_id,))
    db.commit()
    db.close()
