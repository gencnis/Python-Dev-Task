
from app import my_db, Person

def view_data():
    with my_db.session_scope() as session:
        persons = session.query(Person).all()

        for person in persons:
            print(person)

if __name__ == '__main__':
    view_data()
