class SchemaValidator:
    def __init__(self):
        self.PYTHON_TYPES  = {
        "STRING": str,
        "INTEGER": int,
        "BOOLEAN": bool,
        "ARRAY": list,
        "OBJECT": dict,
        }

    def check_schema(self ,value, schema, where="reply"):
    #any mismatch will be stored in this problem list, if the list is empty it means there is no mismatch
        problems = []

        # Check if  value is empty, only allowed if the schema states its "nullable"
        if value is None:
            if not schema.get("nullable"):
                problems.append(f"{where} is empty")
            return problems

        # Check type
        if not isinstance(value, self.PYTHON_TYPES[schema["type"]]):
            problems.append(f"{where} has the wrong type")
            return problems

        # Check if there is enum and if the value is what is allowed by enum
        if "enum" in schema and value not in schema["enum"]:
            problems.append(f"{where} is not allowed: {value}")

        # Check if number is within range
        if "minimum" in schema and value < schema["minimum"]:
            problems.append(f"{where} is too small: {value}")
        if "maximum" in schema and value > schema["maximum"]:
            problems.append(f"{where} is too big: {value}")

        # Check if list does not have more items than maxItems allows
        if schema["type"] == "ARRAY":
            if "maxItems" in schema and len(value) > schema["maxItems"]:
                problems.append(f"{where} has too many items")
            #check every item in list with check_schema function again
            for item in value:
                problems += self.check_schema(item, schema["items"], where + " item")

        # Check if all keys under required exists
        if schema["type"] == "OBJECT":
            for key in schema["required"]:
                if key not in value:
                    problems.append(f"{where} is missing '{key}'")
            #check each key values with check_schema function again
            for key in schema["properties"]:
                if key in value:
                    problems += self.check_schema(value[key], schema["properties"][key], where + "." + key)
    #returns problems that was picked up 
        return problems