# output_schema.py


class OutputSchema:
    #Description rules for the conflict and insight description found in ingridient tree and its children node
    conflict_description="Max 6 words, the reason only. Do not repeat the ingredient name. Null on Safe nodes and on parents that are Trigger only because of a child."
    insight_description="Max 12 words, only if this stall's practice changes this component's risk. Null otherwise. Always null on the dish node."
 
    #Description rules for the users allergies conflict, this includes the user restriciton , allergent ingridient and  whether there is a ingridient (confirm or possible)
    conflict_restriction_description="Copy the user's restriction name EXACTLY, without the severity in brackets."
    conflict_ingredient_description="Max 6 words: the ingredient, sauce or equipment in this dish that carries it."
    conflict_presence_description="CONFIRMED if it is a standard ingredient of this stall's version. POSSIBLE if hidden, only likely, or via cross-contact."


    # This schema node enforces the reply output of the allergy conflicts from the API
    allergy_conflict_schema = {
        "type": "OBJECT",
        "properties": {
            #restriction ,ingredient and presence conflict description rules is defined in a varable, which acts as "2nd prompt" to urge the api to reply in the conditions we set
            "restriction": {"type": "STRING", "description": conflict_restriction_description},
            "ingredient": {"type": "STRING", "description": conflict_ingredient_description},
            #enum, only "CONFIRMED/POSSIBLE" allowed
            "presence": {"type": "STRING", "enum": ["CONFIRMED", "POSSIBLE"], "description": conflict_presence_description},
        },
        #These keys must be included in the API reply
        "required": ["restriction", "ingredient", "presence"],
    }

   # Enforces the final level of the output tree, detailing individual ingredients used within each component
    leaf_node_schema = {
        "type": "OBJECT",
        "properties": {
            "name": {"type": "STRING"},
            #enum, only "Safe/Trigger" allowed
            "status": {"type": "STRING", "enum": ["Safe", "Trigger"]},
            "conflict": {"type": "STRING", "nullable": True, "description": conflict_description},
            "stall_insight": {"type": "STRING", "nullable": True, "description": insight_description},
        },
        #These keys must be included in the API reply
        "required": ["name", "status", "conflict", "stall_insight"],
        }

    # This schema node should enforce the second level of the output tree which shows the components of a dish, It holds a 'children' key which values is in a array. Its schema is defined in the leaf_node_schema dictionary
    component_node_schema = {
    "type": "OBJECT",
    "properties": {
        "name": {"type": "STRING"},
        "status": {"type": "STRING", "enum": ["Safe", "Trigger"]},
        "conflict": {"type": "STRING", "nullable": True, "description": conflict_description},
        "stall_insight": {"type": "STRING", "nullable": True, "description": insight_description},
        "children": {
            "type": "ARRAY",# children is a array
            "items": leaf_node_schema,#Each item in the list is a ingredient
        },
    },
    #These keys must be included in the API reply
    "required": ["name", "status", "conflict", "stall_insight", "children"],
    }
       
    # This schema node should enforce the first level of the output tree which shows the dish. It holds a 'children' key which values is in a array. Its schema is defined in the component_node_schema dictionary
    ingredient_tree_schema = {
        "type": "OBJECT",
        "properties": {
            "name": {"type": "STRING"},
            "status": {"type": "STRING", "enum": ["Safe", "Trigger"]},
            "conflict": {"type": "STRING", "nullable": True, "description": conflict_description},
            "stall_insight": {"type": "STRING", "nullable": True, "description": insight_description},
            "children": {
                "type": "ARRAY",# children is a array
                "items": component_node_schema,#Each item in the list is a component of a dish
            },
        },
        #These keys must be included in the API reply
        "required": ["name", "status", "conflict", "stall_insight", "children"],
    }
    
    # Enforces the reply to be in this JSON structure with every key in the "required" list, using the types listed in the dictionary.(etc string,boolean,integers and enum values depending on what is specified, such as low,medium,high)
    ai_output_schema = {
        "type": "OBJECT",
        "properties": {
            "stall_knowledge": {"type": "STRING", "enum": ["Known", "Inferred", "Unknown"]},
            "is_safe": {"type": "BOOLEAN"},
            "risk_level": {"type": "STRING", "enum": ["Low", "Medium", "High"]},
            "risk_score": {"type": "INTEGER", "minimum": 0, "maximum": 100},
            "stall_specific_insights": {"type": "STRING"},
            "reasoning": {"type": "STRING"},
            "hidden_ingredients": {"type": "ARRAY", "items": {"type": "STRING"}},
            "cross_contact_risks": {"type": "ARRAY", "items": {"type": "STRING"},"maxItems": 3},
            "dietary_status": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "requirement": {
                            "type": "STRING",
                            "description": "Name of a lifestyle or religious requirement the user listed",
                        },
                        "status": {
                            "type": "STRING",
                            "enum": ["COMPLIANT", "NON-COMPLIANT", "UNCERTAIN"],
                        },
                    },
                    "required": ["requirement", "status"],
                },
            },
             # Each item is one allergy conflict object 
            "allergy_conflicts": {"type": "ARRAY", "items":  allergy_conflict_schema},
            # Defines the dish itself from a seperate dictionary
            "ingredient_tree": ingredient_tree_schema,
        },
        #These keys must be included in the API reply
        "required": [
            "stall_knowledge",
            "is_safe",
            "risk_level",
            "risk_score",
            "stall_specific_insights",
            "reasoning",
            "hidden_ingredients",
            "cross_contact_risks",
            "dietary_status",
            "allergy_conflicts",
            "ingredient_tree",
        ],
    }
        
 
