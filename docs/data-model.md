# Climate Emergency Declaration tracking site:  Data Model

The aim of the CED tracking site is to maintain an up-to-date dataset of all governments at all levels in all countries of the world which have declared a Climate Emergency. An important aspect of this aim is to produce a relatively accurate estimate of the population currently living in these government areas.

## Country

The top-level object in the data model is the Country. The CED database is seeded with data on countries of the world based on ISO3166, some of which have been renamed or deleted in the live site, and population data from the World Bank. Each country has a separate government stucture and population count, with no over-arching object to connect them (though individual country populations can obviously be summed to give a global population). 

Fields common to all or most objects, such as `description`, `admin_notes` and `links`, are available for countries.

Country objects are not intended to be created or deleted via the UI, but should be created by the initial database seeding process.

## Structure

Each country must have a "government structure" configured for it, which consists of one or more Structure objects in a simple hierarchical tree relationship. Structures define a template for the geographical and governmental organisation of each country. There is a single Structure at the top of the tree in each country, which is created as part of the database seeding process, and called "National Government" by default (see `govtrack/fixtures/structures.json`. The site administrator can rename this and add child Structure elements, up to as many levels as are needed, to define the type of geographical regions and levels of government applicable for each country.

Structures define the *type* of regions and governments that a country has, whereas Areas are the *actual* regions and governments. Before an Area can be added to the database, the appropriate Structure must be defined for it.

Structures can only be added hierarchically, from the top down - i.e. to add a type of local government at level 4 in the hierarchy, the structures at levels 2 and 3 would need to be added first.

## Area

An Area is a representation of an actual geographic area or governmental organisation in a country, for example Far North Queensland (geographical), Herzogenrath City Council (governmental) or Argentina (governmental). Each Area must correspond to a particular Structure, such as Region, Municipality or National Government.

Areas are defined in a hierarchical relationship similar to Structures, in that they can only be created by adding a child Area to an existing parent. An important difference though is that an Area can have more than one parent Area. Each Area has a single 'direct' parent, but then may have any number of additional 'supplementary' parent Areas

A top-level Area is created for each country when the database is seeded, linked to the default "National Government" Structure.

Each Area is linked directly to its Country, and has other attributes including population, location (a general text description of its geographical context), description, admin notes and links.

## Declaration

Each Area can have zero or more associated Declaration objects, each of which represents an event on a specific date which relates to a Climate Emergency Declaration. Any Area can have a declaration event attached, but in reality only governmental Areas (not Areas that represent geographical regions) would have them.

The most common type of declaration event is of course the official declaration of Climate Emergency by a government. In this case, the declaration would have status "Declared" and may have attributes such as summary, declaration type (e.g. legislative), description and key contact.

Other types of declaration events record when a motion to declare is rejected, or a previous declaration is revoked.

A government Area is considered to have an active declaration if its most recent declaration event has status "Declared". If any other status is most recent, the Area is considered not to have an active declaration.

## Link

Any of the above four objects may have zero or more associated Links, which consist simply of a URL. This enables tracking of resources which may relate to governmental structure for a country, specific declaration motions or other details.


