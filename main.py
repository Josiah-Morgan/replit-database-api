import os
import json

from flask import Flask, jsonify, request
from functools import wraps
import replit
import logging

app = Flask(__name__)

if not app.debug:
    file_handler = logging.FileHandler("flask.log")
    file_handler.setLevel(logging.DEBUG)  # Log all messages
    app.logger.addHandler(file_handler)

database_key = os.environ.get('DATABASE_KEY')

def require_api_key(view_func):
    @wraps(view_func)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('Authorization')

        if api_key == database_key:
            return view_func(*args, **kwargs)
        else:
            return jsonify({'error': 'Unauthorized'}), 401

    return decorated

@app.route('/')
def home():
  return str(len(replit.db.keys()))

# mass deleting, for debuging
@app.route('/f', methods = ['GET'])
@require_api_key
def f():
    data = {}
    for key in replit.db.keys():
        del replit.db[key]

    return jsonify(data), 200

# GET route for getting all key-value pairs in the database
@app.route('/db', methods = ['GET'])
@require_api_key
def get_all_data():
    data = {}
    for key in replit.db.keys():
        value = replit.db[key]
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            pass
        data[key] = value

    return jsonify(data), 200


# GET route for getting the value associated with a specific key
@app.route('/db/<key>', methods=['GET'])
@app.route('/db/<key>/<path:path>', methods=['GET'])
@require_api_key
def get_db_key(key, path = None):
    value = replit.db.get(key)

    if value is None:
        return jsonify({'error': 'Key not found'}), 404

    try:
        value = json.loads(value)
    except json.JSONDecodeError:
        pass

    if path:
        try:
            for part in path.split('/'):
                value = value[part]
        except (KeyError, TypeError):
            return jsonify({'error': 'Invalid value specified'}), 400

        return jsonify(value), 200
  
    return jsonify(value), 200


# GET route to list all keys with a prefix
@app.route('/db_prefix/<prefix>', methods = ['GET'])
@require_api_key
def get_db_prefix(prefix = None):
     
    matches = replit.db.prefix(prefix) 
    return jsonify(matches), 200


# GET route to list all keys
@app.route('/db_keys/', methods = ['GET'])
@require_api_key
def get_db_keys():
    keys = list(replit.db.keys())
    return jsonify(keys), 200


# POST route for adding a new key-value pair to the database
@app.route('/db', methods = ['POST'])
@require_api_key
def add_to_db():
  
    if not request.json or 'key' not in request.json or 'value' not in request.json:
        return jsonify({'error': 'Invalid input'}), 400
        app.logger.error("Invaild input: add_to_db")
      
    key = request.json['key']
    value = request.json['value']
    if isinstance(value, (dict, list)):
        value = json.dumps(value)

    replit.db[key] = value

    try:
        value = json.loads(value)
    except json.JSONDecodeError:
        pass

    return jsonify({key: value}), 201

# Chatgpt for the win!, chatgpt made this function what a smart ai
def merge_dicts(old_dict, new_dict):
    for key, value in new_dict.items():
        if key in old_dict:
            if isinstance(old_dict[key], list) and isinstance(value, list):
                #unique_elements = set(old_dict[key] + value)
                # Convert the set back to a list and assign it to the key
                #old_dict[key] = list(unique_elements)
                old_dict[key].extend(value)
              
            elif isinstance(old_dict[key], dict) and isinstance(value, dict):
                merge_dicts(old_dict[key], value)
            else:
                old_dict[key] = value 
        else:
            old_dict[key] = value  

    return old_dict

# PUT route for updating an existing key-value pair in the database
@app.route('/db/<key>', methods = ['PUT'])
@require_api_key
def update_db(key):
    if key not in replit.db.keys():
        return jsonify({'error': 'Key not found'}), 404
        app.logger.error("Key not found: update_db")
    
    old_value = replit.db[key]
    try:
        old_value = json.loads(old_value)
    except (TypeError, json.JSONDecodeError):
        pass
  
    new_value = request.json.get('value', {})

    if isinstance(new_value, (dict, list)):
        new_value = json.dumps(new_value)

    try:    
        new_value_dict = json.loads(new_value)

        # Merge the old and new values recursively
        merged_dict_ = merge_dicts(old_value, new_value_dict)
        new_value = json.dumps(merged_dict_)

    except (TypeError, json.JSONDecodeError):
        pass

    replit.db[key] = new_value
    
    try:
        new_value = json.loads(new_value)
    except (TypeError, json.JSONDecodeError):
        pass

    return jsonify({key: {'value': new_value}}), 200


@app.route('/db/<key>', methods=['DELETE'])
@app.route('/db/<key>/<path:path>', methods=['DELETE'])
@require_api_key
def delete_from_db(key, path = None):
    if key not in replit.db.keys():
        return jsonify({'error': 'Key not found'}), 404
        app.logger.error(f"Key not found: {key} (delete_from_db)")
    
    value = replit.db[key]
    try:
        value = json.loads(value)
    except json.JSONDecodeError:
        pass  

    # /db/FranchiseRoles - deletes the whole table
    if not path:
        del replit.db[key]
        return jsonify({key: value}), 200

    path_elements = path.split('/')

    # /db/FranchiseRoles/817569246103470110 - deletes a whole key
    if len(path_elements) == 1:
        item = ''.join(path_elements)
        if item not in value:
            return jsonify({'error': 'Key not found'}), 404
        del value[item]
      
        if not value:
          del replit.db[key]
        else:
          replit.db[key] = json.dumps(value)
          
        return jsonify({key: value}), 200

    # /db/FranchiseRoles/817569246103470110/role_id - deletes something in a list or dict
    # /db/FranchiseRoles/817569246103470110/some_dict/some_dict_value - deletes a nested value

    def traverse_and_delete(obj, elements):
        if not elements:
            return obj

        current_element = elements[0]

        if isinstance(obj, dict) and current_element in obj:
            if len(elements) == 1: 
                del obj[current_element]
            else:
                traverse_and_delete(obj[current_element], elements[1:])
        elif isinstance(obj, list):
            try:
                index = current_element
                if len(elements) == 1:
                    print(index)
                    try:
                      obj.remove(index)
                    except ValueError:
                      try:
                        obj.pop(int(index))
                      except IndexError:
                        return jsonify({'error': 'Invalid path'}), 400
                else:
                    traverse_and_delete(obj[index], elements[1:])
            except (ValueError, IndexError):
                return jsonify({'error': 'Invalid path'}), 400

            obj = [item for item in obj if item]

        if isinstance(obj, dict):
           obj = {k: v for k, v in obj.items() if v}
      
        if isinstance(obj, (list, dict)) and not obj:
            return None

        return obj

    value = traverse_and_delete(value, path_elements)
    if value is None:
        del replit.db[key]
    else:
        replit.db[key] = json.dumps(value)

    return jsonify({key: value}), 200


port = int(os.environ.get('PORT', 8080))
app.run(host='0.0.0.0', port=port)
