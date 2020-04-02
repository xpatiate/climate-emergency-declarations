#!/usr/bin/env python3

import logging
import sys

# any cmd-line argument turns loglevel up to debug
loglevel = logging.INFO
if len(sys.argv) > 1:
    loglevel = logging.DEBUG
logging.basicConfig(level=loglevel)


class Node:
    """Define a node in a tree structure, generally a government of some kind.
    Each node has name, population and a flag indicating whether it has made a
        declaration.
    Each node object (other than the root) has a main parent, and potentially 
        other parents via an indirect relationship.
    Node children are linked either via direct or indirect parent
        relationships.
    Each node specifies its own population. The population of a parent node 
    should in theory be the sum of all its child node populations, but is
    not guaranteed to be so. 
    """

    def __init__(self, name, population, parent):
        self.name = name
        self.population = population
        self.parent = parent
        self.extra_parents = set()
        self.is_declared = False
        self.children = set()

    def __str__(self):
        return self.name

    def declare(self):
        self.is_declared = True

    def add_child(self, name, population):
        """ Create a new Node which this node is the direct parent of."""
        child = Node(name, population, self)
        self.children.add(child)
        return child

    def add_parent(self, parentnode):
        """ Add an indirect parent relationship to this node."""
        self.extra_parents.add(parentnode)
        parentnode.children.add(self)

    def descendants(self, desc_list=None):
        """ Return a complete set of all descendants of this node."""
        if not desc_list:
            desc_list = set()
        for child in self.children:
            desc_list.add(child)
            desc_list.update(child.descendants(desc_list))
        return desc_list

    def ancestors(self, asc_list=None):
        """ Return a complete set of all ancestors of this node."""
        if not asc_list:
            asc_list = set()
        if self.parent:
            allparents = [self.parent]
            if len(self.extra_parents):
                allparents.extend(list(self.extra_parents))
            for parent in allparents:
                asc_list.add(parent)
                asc_list.update(parent.ancestors(asc_list))
        return asc_list

    def simple_declared_population(self, total=0):
        """Straight-forward population count: count all declared nodes without
        also counting their descendants. If any node is not declared, recurse
        through its children. Count the full population for any declared
        node."""
        if self.is_declared:
            total += self.population
        else:
            for child in self.children:
                total = child.simple_declared_population(total)
        return total

    def declared_population(self, total=0, counted=None):
        """More complex population count which tries to avoid double-counting
        in structures where some nodes appear more than once, due to having
        multiple parents."""
        if not counted:
            counted = set()

        # Node is declared so we want to count its population
        if self.is_declared:
            # First check if any descendants of this node have already been counted
            current_desc = self.descendants()
            overlap = current_desc.intersection(counted)
            logging.debug(
                "%s: current descendants [%s], counted [%s], overlap [%s]"
                % (self.name, len(current_desc), len(counted), len(overlap))
            )

            if not overlap:
                # No descendants of this node have been counted yet,
                # so just add the whole population,
                # and add all its descendants to the 'already counted' list
                total += self.population
                counted.add(self)
                counted.update(self.descendants())

            else:
                # Some descendants have already been counted, so we need to
                # subtract their population from the total population for this node.
                subtotal = self.population
                for node in overlap:

                    # only subtract the populations of nodes immediately
                    # under the current node, not any from further down the branch
                    # XXX seems like this could be incorrect if overlapping happens
                    # at a lower level in the tree
                    if node in self.children:
                        logging.debug(
                            "subtracting %s from %s for %s"
                            % (node.population, subtotal, node.name)
                        )
                        subtotal -= node.population
                    else:
                        logging.debug(
                            "NOT subtracting %s from %s for %s because not a direct child"
                            % (node.population, subtotal, node.name)
                        )

                # The total we're adding for this node is now
                # [ this node's population ] minus [ any immediate children already counted ]
                total += subtotal

        else:
            # This node hasn't declared, so look at its children
            # (both direct and indirect)
            for child in self.children:
                (total, counted) = child.declared_population(total, counted)

        return (total, counted)

    def num_declared_ancestors(self):
        num_declared = 0
        for parent in self.ancestors():
            if parent.is_declared:
                num_declared += 1
        return num_declared

    def total_node_contributions(self):
        total = 0
        for node in self.descendants():
            node_contrib = node.contribution()
            total += node_contrib
            logging.debug(
                "node %s, population %s, contribution %s, total %s"
                % (node.name, node.population, node.contribution(), total)
            )
        return total

    def contribution(self):
        node_total = 0
        if self.is_declared and self.num_declared_ancestors() == 0:
            node_total = self.population
        elif self.num_declared_ancestors() > 1:
            node_total = -1 * (self.num_declared_ancestors() - 1) * self.population
        return node_total

    def print_tree(self, level=1):
        if level == 1:
            Node.print_row(
                "", "Name", "D", "Popn", "Contrib", "Ancestors", "Descendants"
            )
        Node.print_node(self, level)
        level += 1
        for child in self.children:
            Node.print_tree(child, level)

    NAME_COL = 24
    POP_COL = 4
    POP_CON = 7
    ANC_COL = 10
    DEC_COL = 12

    @staticmethod
    def print_node(node, level):
        dashes = "-" * level
        decl = " "
        if node.is_declared:
            decl = "*"
        Node.print_row(
            dashes,
            node.name,
            decl,
            node.population,
            node.contribution(),
            len(node.ancestors()),
            len(node.descendants()),
        )

    @staticmethod
    def print_row(dashes, name, declared, popn, contrib, anc, dec):
        name_len = Node.NAME_COL - len(dashes)
        format_name = ("{: <%d}" % name_len).format(name)
        format_pop = ("{: >%d}" % Node.POP_COL).format(popn)
        format_con = ("{: >%d}" % Node.POP_CON).format(contrib)
        format_anc = ("{: >%d}" % Node.ANC_COL).format(anc)
        format_dec = ("{: >%d}" % Node.DEC_COL).format(dec)
        print(
            "%s %s%s %s\t%s\t%s %s"
            % (
                dashes,
                format_name,
                declared,
                format_pop,
                format_con,
                format_anc,
                format_dec,
            )
        )


def simple_tree():
    """ Create a simple tree with three levels, and no multi-parent relationships."""
    root = Node("L1", 60, None)

    l2a = root.add_child("L2A", 30)
    l2b = root.add_child("L2B", 20)
    l2c = root.add_child("L2C", 10)

    l3a1 = l2a.add_child("L3A1", 15)
    l3a2 = l2a.add_child("L3A2", 10)
    l3a3 = l2a.add_child("L3A3", 5)
    l3b1 = l2b.add_child("L3B1", 20)
    l3b1a = l3b1.add_child("L3B1A", 10)
    l3b1b = l3b1.add_child("L3B1B", 10)

    l2a.declare()
    l3b1.declare()
    l3b1a.declare()

    print("*** Simple tree")
    root.print_tree()

    (total, counted) = root.declared_population()
    print("Declared population: %s" % total)
    print(
        """    Nodes L2A (30) and L3B1 (20) have declared, so total population is
    the sum of the population of those two nodes. Node L3B1A has also declared, 
    but is not counted because it is covered by L3B1."""
    )
    print("Via individual nodes: %s" % root.total_node_contributions())
    print()


def multi_parents_two():
    root = Node("L1", 40, None)

    l2a = root.add_child("L2A", 40)
    l2b = root.add_child("L2B", 20)

    l3a1 = l2a.add_child("L3A1", 10)
    l3a2 = l2a.add_child("L3A2", 10)
    l3a3 = l2a.add_child("L3A3", 10)
    l3a4 = l2a.add_child("L3A4", 10)

    l3a3.add_parent(l2b)
    l3a4.add_parent(l2b)

    l2a.declare()
    l2b.declare()

    print("*** Two-level tree with overlapping nodes")
    root.print_tree()

    (total, counted) = root.declared_population()
    print("Declared population: %s" % total)
    print(
        """    Both top-level nodes have declared, but two nodes (L3A3 and L3A4) are
    linked to both parents, so must not be counted twice. Their population
    counts are subtracted from the count to give a total of 40."""
    )
    print("Via individual nodes: %s" % root.total_node_contributions())
    print()


def multi_parents_three():
    root = Node("L1", 40, None)

    l2a = root.add_child("L2A", 40)
    l2b = root.add_child("L2B", 20)

    l3a1 = l2a.add_child("L3A1", 10)
    l3a2 = l2a.add_child("L3A2", 10)
    l3a3 = l2a.add_child("L3A3", 10)
    l3a4 = l2a.add_child("L3A4", 10)

    l3a41 = l3a4.add_child("L3A41", 5)
    l3a42 = l3a4.add_child("L3A42", 5)

    l3a3.add_parent(l2b)
    l3a4.add_parent(l2b)

    l2a.declare()
    l2b.declare()

    print("*** Three-level tree with overlapping nodes")
    root.print_tree()

    (total, counted) = root.declared_population()
    print("Declared population: %s" % total)
    print(
        """    Both top-level nodes have declared, but two nodes (L3A3 and L3A4) are
    linked to both parents, so must not be counted twice. Their population
    counts are subtracted from the count to give a total of 40. The nodes at the 
    next level down (L3A41 and L3A42) are not also subtracted because they are not
    immediate children of the declared node."""
    )
    print("Via individual nodes: %s" % root.total_node_contributions())
    print()


def uzbekistan():
    root = Node("UZB", 4, None)

    t1a = root.add_child("1_T1A", 2)
    t1r = root.add_child("1_T1R", 4)

    t2r1 = t1r.add_child("1_T2R", 1)
    t2r2 = t1r.add_child("2_T2R", 1)
    t2r3 = t1r.add_child("3_T2R (overlap)", 1)
    t2r4 = t1r.add_child("4_T2R (overlap)", 1)

    t2r3.add_parent(t1a)
    t2r4.add_parent(t1a)

    t1r.declare()
    t1a.declare()

    print("*** Three-level tree with overlapping nodes modelled on UZB from test data")
    root.print_tree()

    (total, counted) = root.declared_population()
    print("Declared population: %s" % total)
    print("Via individual nodes: %s" % root.total_node_contributions())
    print()


if __name__ == "__main__":
    simple_tree()
    print()
    multi_parents_two()
    print()
    multi_parents_three()
    print()
    uzbekistan()
