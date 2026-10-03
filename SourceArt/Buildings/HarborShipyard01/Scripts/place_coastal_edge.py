from pathlib import Path
p=Path(__file__).with_name('import_unreal.py')
exec(compile(p.read_text().split('\ndef ready(')[0],str(p),'exec'))
world=u.EditorLoadingAndSavingUtils.load_map(map_filename(SETTLEMENT_MAP))
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
for actor in actors.get_all_level_actors():
    if not actor.actor_has_tag('HarborShipyard01'):continue
    label=actor.get_actor_label()
    if label=='Harbor coastal land':actor.set_actor_location(u.Vector(0,-2200,-65),False,False)
    elif label=='Harbor distant sea':actor.set_actor_location(u.Vector(0,16000,-103),False,False)
    elif isinstance(actor,u.StaticMeshActor):
        actor.set_actor_location(actor.get_actor_location()+u.Vector(3200,2600,0),False,False)
require(u.EditorLoadingAndSavingUtils.save_map(world,SETTLEMENT_MAP),'Could not save clear coast placement')
capture()
