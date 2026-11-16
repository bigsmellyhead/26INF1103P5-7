# ingredient_tree_processor.py

# Cleans up and reads the ingredient tree, so the rules in LogicManager only deal with scores and statuses
class IngredientTreeProcessor:

    # Removes a child that just repeats its parent's name (e.g. Rice > Rice), keeping its verdict on the parent
    def remove_repeated_children(self, node: dict) -> None:
        if "children" not in node:
            return
        kept = []
        for child in node["children"]:
            if child["name"].strip().lower() == node["name"].strip().lower():
                if child["status"] == "Trigger":
                    node["status"] = "Trigger"
                    node["conflict"] = node["conflict"] or child["conflict"]
                # the repeated child may have its own children, so keep those
                kept.extend(child.get("children", []))
            else:
                kept.append(child)
        node["children"] = kept
        for child in node["children"]:
            self.remove_repeated_children(child)

    # Walks the ingredient tree (children first), keeps parents consistent and collects every Trigger node
    def collect_triggers(self, node: dict, found: list, flags: list) -> list:
        # leaf nodes have no "children" key, so .get is used
        for child in node.get("children", []):
            self.collect_triggers(child, found, flags)

        child_triggered = any(child["status"] == "Trigger" for child in node.get("children", []))

        # A parent is a Trigger if anything below it is
        if child_triggered and node["status"] == "Safe":
            node["status"] = "Trigger"

        if node["status"] == "Trigger":
            # A Trigger needs a reason somewhere: its own, or one of its children's
            if not node["conflict"] and not child_triggered:
                node["conflict"] = "Flagged by the AI (no detail given)"
                flags.append(f"'{node['name']}' was marked Trigger without a reason.")
            found.append(node)
        return found
