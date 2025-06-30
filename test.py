from tol.sources.benchling import benchling
from dotenv import load_dotenv

load_dotenv('.env.dev')


bds = benchling()
import json
# print(bds.schemas)
#print(json.dumps(bds.relationship_config, indent=2, default=str))


# worklists = bds.get_list('worklist')
# print(next(worklists).attributes)

tubes = bds.get_list('tissue')
contents = bds.get_to_many_relations(next(tubes), 'container_contents')
print(next(contents))


#print(bds.get_to_many_relations(next(tubes), 'container_content'))

# for well in wells:
#     print(well.relationships)
#     print('---')