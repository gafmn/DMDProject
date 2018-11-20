from flask import Flask, jsonify, request
import sqlite3
import logging
from flask_restplus import Api, Resource, fields

logging.basicConfig(level=logging.DEBUG)
from faker import Faker

app = Flask(__name__)
# define api
api = Api(app)
app.config["SWAGGER_UI_JSONEDITOR"] = True
DB_FILE = 'carsharing.sqlite'
datagen = Faker()

sql_create_tasks_table = """CREATE TABLE IF NOT EXISTS tasks(
                                id integer UNIQUE PRIMARY KEY,
                                name varchar(50) NOT NULL,
                                priority integer,
                                end_date date NOT NULL
                            );"""

sql_create_charging_station_table = """CREATE TABLE IF NOT EXISTS charging_station(
                                            UID integer UNIQUE PRIMARY KEY,
                                            amount_of_available_slots integer NOT NULL,
                                            time_of_charging time NOT NULL, 
                                            price double
                                            GPS_location varchar(25) NOT NULL 
                            );"""

sql_create_charging_plugs = """CREATE TABLE IF NOT EXISTS charging_plugs(
                                plug_id integer PRIMARY KEY ,
                                shape_plug varchar(20) not null  ,
                                size_plug int(10) not null 
                            );"""

sql_create_have_plugs = """CREATE TABLE IF NOT EXISTS have_plugs(
                                            UID integer NOT NULL,
                                            plug_id integer NOT NULL,
                                            FOREIGN KEY (UID)  references charging_station(UID),
                                            FOREIGN KEY (plug_id)  references charging_plugs(plug_id),
                                            PRIMARY KEY (UID, plug_id)
                                );"""

sql_create_provider_table = """CREATE TABLE IF NOT EXISTS provider(
                                    company_id integer PRIMARY KEY,
                                    address varchar(25) NOT NULL,
                                    phone_number varchar(25),
                                    name_company varchar(25)

                        );"""

sql_create_customers_table = """CREATE TABLE IF NOT EXISTS customers (
                                  username  varchar(20) UNIQUE PRIMARY KEY ,
                                  email  varchar(20) not null ,
                                  cardnumber    varchar(20) not null,
                                  fullname   varchar(50) not null,
                                  phone_number varchar(15),
                                  zip integer not null ,
                                  city varchar(20) not null ,
                                  country varchar(50) not null 

                                  
                        );"""

#TODO cost and duration?
#TODO st_point, pick location same?
sql_create_orders = """CREATE TABLE IF NOT EXISTS orders (
                        order_id integer UNIQUE PRIMARY KEY,
                        date text not null ,
                        time text not null ,
                        date_closed text not null,
                        duration integer,
                        status varchar(10) not null ,
                        cost integer,
                        st_point varchar(50) not null ,
                        destination varchar(50) not null ,
                        car_location varchar(50) not null, 
                        
                        foreign key (order_id) references customers(username)
                        
                    );"""

sql_create_cars = """CREATE TABLE IF NOT EXISTS cars(
                        car_id integer unique primary key ,
                        gps_location varchar(25) not null ,
                        year varchar(4),
                        reg_num varchar(11) not null ,
                        charge int(1) not null ,
                        available int(1) not null ,
                        
                        foreign key (car_id) references orders(order_id),
                        foreign key (car_id) references models(model_id)
                    );"""

sql_create_charge_car_table = """CREATE TABLE IF NOT EXISTS charge_car(
                                    cost double, 
                                    date date,
                                    car_id integer PRIMARY KEY,
                                    UID integer PRIMARY KEY,
                                    FOREIGN KEY (car_id) references cars(car_id),
                                    FOREIGN KEY (UID) references charging_station(UID)
                        );"""

#TODO Availability of timing( What the type?)
sql_create_workshop_table = """CREATE TABLE IF NOT EXISTS workshop(
                                    WID integer PRIMARY KEY ,
                                    availability_of_timing time NOT NULL,
                                    location varchar(25) NOT NULL
                        );"""

sql_create_repair_car = """CREATE TABLE IF NOT EXISTS repair_car(
                                WID integer,
                                car_id integer unique, 
                                report_id integer PRIMARY KEY,
                                date date,
                                progress_status varchar(10),
                                FOREIGN KEY (WID) references workshop(WID),
                                FOREIGN KEY (car_id) references cars(car_id)
                    );"""

sql_create_models = """CREATE TABLE IF NOT EXISTS models(
                        model_id integer PRIMARY KEY ,
                        name varchar(20) not null,
                        type varchar(30) not null ,
                        service_class varchar(30) not null ,
                        
                        foreign key (model_id) references cars(car_id),
                        foreign key (model_id) references charging_plugs(plug_id)
                    );"""

sql_create_part_order_table = """CREATE TABLE IF NOT EXISTS part_order(
                                    date date,
                                    amount integer,
                                    cost double,
                                    order_id integer PRIMARY KEY ,
                                    part_id integer,
                                    WID integer,
                                    company_id integer,
                                    FOREIGN KEY (part_id) references parts(part_id),
                                    FOREIGN KEY (WID) references workshop(WID),
                                    FOREIGN KEY (company_id) references provider(company_id)
                        );"""

sql_create_parts_table = """CREATE TABLE IF NOT EXISTS parts(
                                part_id integer PRIMARY KEY, 
                                type_of_detail varchar(25) NOT NULL,
                                cost double
                        );"""

sql_create_workshop_have_parts_table = """CREATE TABLE IF NOT EXISTS workshop_have_parts(
                                    amount integer,
                                    amount_week_ago integer,
                                    WID integer PRIMARY KEY,
                                    part_id integer PRIMARY KEY, 
                                    FOREIGN KEY (WID) references workshop(WID),
                                    FOREIGN KEY (part_id) references parts(part_id)
                        );"""

sql_create_fit_table = """CREATE TABLE IF NOT EXISTS fit(
                                part_id integer PRIMARY KEY,
                                model_id integer PRIMARY KEY,
                                FOREIGN KEY (part_id) references parts(part_id),
                                FOREIGN KEY (model_id) references models(model_id)
                );"""

sql_create_providers_have_parts_table = """CREATE TABLE IF NOT EXISTS providers_have_parts(
                                                company_id integer PRIMARY KEY,
                                                part_id integer PRIMARY KEY,
                                                FOREIGN KEY (company_id) references provider(company_id),
                                                FOREIGN KEY (part_id) references parts(part_id)
                                );"""
list_tables_to_create=[sql_create_charging_station_table,
                       sql_create_have_plugs,
                       sql_create_provider_table,
                       sql_create_customers_table,
                       sql_create_orders,
                       sql_create_cars,
                       sql_create_charge_car_table,
                       sql_create_workshop_table,
                       sql_create_repair_car,
                       sql_create_models,
                       sql_create_part_order_table,
                       sql_create_parts_table,
                       sql_create_workshop_have_parts_table,
                       sql_create_fit_table,
                       sql_create_fit_table,
                       sql_create_providers_have_parts_table]

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    try:
        conn = sqlite3.connect(db_file)
        logging.info("Successfully connected to database")
        return conn
    except sqlite3.DatabaseError as e:
        print(e)

    return None


def insert_fake_data(conn):
    cursor = conn.cursor()
    try:
        for i in range(10):
            name = str(datagen.name())
            num = str(datagen.random_number(digits=3))
            date = str(datagen.date())
            sql = ''' INSERT INTO tasks(name,priority,end_date)
                          VALUES(?,?,?) '''
            task = (name, num, date)
            cursor.execute(sql, task)
            conn.commit()
        return "Successfull"
    except Exception:
        logging.info("Error while inserting occurs")
    return "Error while inserting occurs"


def modify_fake_data(conn):
    cursor = conn.cursor()
    try:
        sql = '''UPDATE tasks SET name = 'AAAAAAAAAAAAA' WHERE priority < 10000'''
        cursor.execute(sql)
        conn.commit()
        return "Successfully modified"
    except Exception:
        logging.info("Error while updating occurs")
    return "Error while updating occurs"


def select_fake_data(conn, cond):
    cursor = conn.cursor()
    diction = {}
    try:
        sql = "SELECT name FROM tasks WHERE " + cond + " BETWEEN 5005 and 15600"
        cursor.execute(sql)
        i = 0
        for row in cursor.fetchall():
            diction[i] = row[0]
            i += 1
        return diction
    except Exception as e:
        print(e)
        logging.info("Error while selecting occurs")
    return "Error while updating occurs"


# Example of using flask_restplus api
#######################################################################
test = api.model('Test', {'condition': fields.String("Condition...")})


@api.route("/select_fake_data")
class TestSelectFake(Resource):

    @api.expect(test)
    def post(self):
        cond = request.get_json(silent=True)
        conn = create_connection(DB_FILE)
        response = select_fake_data(conn, cond['condition'])
        close_connection(conn)
        return jsonify(response)


@api.route("/modify")
class ModifyFake(Resource):

    def get(self):
        conn = create_connection(DB_FILE)
        response = modify_fake_data(conn)
        close_connection(conn)
        return jsonify(response)


@api.route("/insert")
class InsertFakeData(Resource):

    def get(self):
        conn = create_connection(DB_FILE)
        response = insert_fake_data(conn)
        close_connection(conn)
        return jsonify(response)

########################################################################



def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
        conn.commit()
        logging.info("Successfully created table in database")
    except sqlite3.DatabaseError as e:
        print(e)


def close_connection(conn):
    conn.close()
    logging.info("Successfully closed connection to database")
    return None


@app.before_first_request
def init_db():
    logging.info("Try to connect to database")
    conn = create_connection(DB_FILE)
    logging.info("Try to initialise tables in database")
    for sql_to_create in list_tables_to_create:
        create_table(conn, sql_to_create)

    # create_table(conn, sql_create_tasks_table)
    # conn.commit()
    # insert_fake_data(conn)
    # conn.commit()
    # modify_fake_data(conn)
    # conn.commit()
    # select_fake_data(conn, "priority")
    # conn.commit()
    logging.info("Try to close connection to database")
    close_connection(conn)


@app.route('/')
def hello_world():
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
