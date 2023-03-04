from fastapi import FastAPI
from pydantic import BaseModel
import mysql.connector

app = FastAPI(title="Customer Data Center")

db = mysql.connector.connect(
    host = "localhost",
    user = "root",
    password = "",
    database = "python"
)

order = db.cursor()

class Customer(BaseModel):
    id: int
    name: str
    address: str

@app.get("/customer/", tags=["Read Data"], summary=["Display all customer data"])
async def read_customers():
    order.execute("SELECT * FROM customer")
    result = order.fetchall()
    return result

@app.post("/customer/", tags=["Create Data"], summary=["Create data for customers"])
async def create_customer(customer: Customer):
    order.execute("INSERT INTO customer (id, name, address) VALUES (%s, %s, %s)",(customer.id, customer.name, customer.address))
    db.commit()
    return {"Customer created successfully"}

@app.get("/customer/{id}", tags=["Read Data"], summary=["Display specific customer data"])
async def get_customer(id: int):
    query.execute("SELECT * FROM customer WHERE id= %s", (id,))
    result = query.fetchone()
    return result

@app.delete("/customer/{id}", tags=["Delete Data"], summary=["Delete specific customer data"])
async def delete_customer(id: int):
    query.execute("DELETE FROM customer WHERE id= %s", (id,))
    db.commit()
    return ("Customer deleted successfully")

@app.put("/customer/{id}", tags=["Edit Data"], summary=["Edit all customer data"])
async def update_customer(id: int, customer: Customer):
    order.execute("UPDATE customer SET name = %s, address = %s WHERE id = %s",(customer.name, customer.address, customer.id))
    db.commit()
    return {"data updated successfully"}

@app.patch("/customer/{id}", tags=["Edit Data"], summary=["Edit specific customer data"])
async def patch_customer(id: int, customer: Customer):
    query = "UPDATE customer SET "
    value = []
    if customer.name:
        query += "name=%s, "
        value.append(customer.name)
    if customer.address:
        query += "address=%s, "
        value.append(customer.address)

    query = query[:-2]
    query += " WHERE id=%s"
    value.append(id)
    order.execute(query, tuple(value))
    db.commit()
    return {"data updated successfully"}
    




