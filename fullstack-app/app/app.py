from flask import Flask, request, jsonify
import psycopg2
import redis
import json

app = Flask(__name__)

def get_db():
    return psycopg2.connect(
        host="db",
        database="usersdb",
        user="user",
        password="password"
    )

cache = redis.Redis(host='cache', port=6379, decode_responses=True)

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(100)
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

with app.app_context():
    init_db()

@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data or 'name' not in data or 'email' not in data:
        return jsonify({"error": "Missing name or email"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id",
                (data['name'], data['email']))
    user_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    cache.delete('users_list')
    return jsonify({"id": user_id, "name": data['name'], "email": data['email']}), 201


@app.route('/users', methods=['GET'])
def get_users():
    cached = cache.get('users_list')
    if cached:
        return jsonify(json.loads(cached))
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name, email FROM users")
    rows = cur.fetchall()
    users = [{"id": r[0], "name": r[1], "email": r[2]} for r in rows]
    cache.set('users_list', json.dumps(users), ex=60)
    cur.close()
    conn.close()
    return jsonify(users)


@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name, email FROM users WHERE id = %s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return jsonify({"id": row[0], "name": row[1], "email": row[2]})
    return jsonify({"error": "User not found"}), 404


@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    if not data or ('name' not in data and 'email' not in data):
        return jsonify({"error": "Missing name or email"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE id = %s", (user_id,))
    if not cur.fetchone():
        cur.close()
        conn.close()
        return jsonify({"error": "User not found"}), 404

    name = data.get('name')
    email = data.get('email')
    if name and email:
        cur.execute("UPDATE users SET name = %s, email = %s WHERE id = %s", (name, email, user_id))
    elif name:
        cur.execute("UPDATE users SET name = %s WHERE id = %s", (name, user_id))
    elif email:
        cur.execute("UPDATE users SET email = %s WHERE id = %s", (email, user_id))
    
    conn.commit()
    cur.close()
    conn.close()
    cache.delete('users_list')
    return jsonify({"id": user_id, **data}), 200


@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE id = %s", (user_id,))
    if not cur.fetchone():
        cur.close()
        conn.close()
        return jsonify({"error": "User not found"}), 404

    cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()
    cache.delete('users_list')
    return '', 204


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)