def make_hierarchy(itemlist, seen):
    ordered = []
    # Items are ordered by level, so all the top-level ones come first
    for item in itemlist:
        if not item.id in seen:
            ordered.append(item)
            seen.add(item.id)
        if item.children:
            kidlist = make_hierarchy( item.children, seen )
            ordered.extend( kidlist )
    return ordered
