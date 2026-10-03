"""Execute with the SHŌEN Unreal Editor Python commandlet; genuine FBX/assets.
All generated packages live under /Game/Art/Characters/Samurai/Prototype01.
Never import concurrently with other editor/game processes in this checkout.
"""
import json
from pathlib import Path
import unreal as u

ROOT=Path(u.Paths.project_dir()).resolve().parent
ART=ROOT/'SourceArt/Characters/Samurai/Prototype01'
DEST='/Game/Art/Characters/Samurai/Prototype01'
MANIFEST=json.loads((ART/'asset-manifest.json').read_text())
assets=u.AssetToolsHelpers.get_asset_tools(); edit=u.MaterialEditingLibrary
stat=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
skel=u.get_editor_subsystem(u.SkeletalMeshEditorSubsystem)
report={'imports':[],'warnings':[]}

def load(name):
    obj=u.load_asset(DEST+'/'+name)
    if not obj: raise RuntimeError('Missing required imported asset '+name)
    return obj

def import_file(path,name,kind='texture',skeleton=None):
    task=u.AssetImportTask(); task.filename=str(path); task.destination_path=DEST
    task.destination_name=name; task.automated=True; task.replace_existing=True; task.save=True
    if kind!='texture':
        options=u.FbxImportUI(); options.automated_import_should_detect_type=False
        options.import_materials=False; options.import_textures=False
        options.import_mesh=kind!='animation'; options.import_animations=kind=='animation'
        options.import_as_skeletal=kind in ('skeletal','animation')
        options.mesh_type_to_import=u.FBXImportType.FBXIT_ANIMATION if kind=='animation' else u.FBXImportType.FBXIT_SKELETAL_MESH if kind=='skeletal' else u.FBXImportType.FBXIT_STATIC_MESH
        if skeleton: options.skeleton=skeleton
        options.create_physics_asset=False
        data=options.anim_sequence_import_data if kind=='animation' else options.skeletal_mesh_import_data if kind=='skeletal' else options.static_mesh_import_data
        data.set_editor_property('convert_scene',False)
        data.set_editor_property('convert_scene_unit',True)
        data.set_editor_property('force_front_x_axis',False)
        if kind!='animation':
            data.set_editor_property('normal_import_method',u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
        if kind=='static':
            data.combine_meshes=True; data.auto_generate_collision=False; data.generate_lightmap_u_vs=False
        if kind=='animation':
            data.set_editor_property('animation_length',u.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME)
        task.options=options; task.factory=u.FbxFactory()
    assets.import_asset_tasks([task])
    if not task.imported_object_paths: raise RuntimeError('Import failed: '+str(path))
    report['imports'].append({'source':str(path.relative_to(ROOT)),'assets':list(task.imported_object_paths)})
    return load(name)

# Re-importing the same generated names is intentional and reproducible.
textures={}
for name in ['T_Samurai_BaseColor','T_Samurai_Normal','T_Samurai_ORM']:
    tex=import_file(ART/'textures'/(name+'.png'),name)
    if name.endswith('Normal'):
        tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_NORMALMAP)
        tex.set_editor_property('srgb',False)
        # Blender generated OpenGL +Y tangent normals; Unreal expects -Y.
        tex.set_editor_property('flip_green_channel',True)
    elif name.endswith('ORM'):
        tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_MASKS); tex.set_editor_property('srgb',False)
    textures[name]=tex
for lod in range(3):
    for type_ in ('Position','Normal'):
        name=f'T_VAT_{type_}_LOD{lod}'; tex=import_file(ART/'textures'/(name+'.exr'),name)
        tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_HDR)
        tex.set_editor_property('srgb',False); tex.set_editor_property('mip_gen_settings',u.TextureMipGenSettings.TMGS_NO_MIPMAPS)
        tex.set_editor_property('filter',u.TextureFilter.TF_NEAREST)
        tex.set_editor_property('never_stream',True)
        tex.set_editor_property('address_x',u.TextureAddress.TA_CLAMP); tex.set_editor_property('address_y',u.TextureAddress.TA_CLAMP)
        textures[name]=tex

def new_asset(name,cls,factory):
    old=u.load_asset(DEST+'/'+name)
    return old if old else assets.create_asset(name,DEST,cls,factory)
def expr(mat,cls,**kwargs):
    n=edit.create_material_expression(mat,cls)
    for k,v in kwargs.items(): n.set_editor_property(k,v)
    return n
def link(a,out,b,inp):
    if not edit.connect_material_expressions(a,out,b,inp): raise RuntimeError(f'Material connection failed: {out} -> {inp}')
def prop(n,out,p):
    if not edit.connect_material_property(n,out,p): raise RuntimeError('Material property connection failed')
def scalar(mat,name,value): return expr(mat,u.MaterialExpressionScalarParameter,parameter_name=name,default_value=value)

def atlas_material(name,animated):
    mat=new_asset(name,u.Material,u.MaterialFactoryNew())
    edit.delete_all_material_expressions(mat)
    mat.set_editor_property('two_sided',False)
    mat.set_editor_property('tangent_space_normal',not animated)
    color=expr(mat,u.MaterialExpressionTextureSampleParameter2D,parameter_name='BaseColor',texture=textures['T_Samurai_BaseColor'])
    orm=expr(mat,u.MaterialExpressionTextureSampleParameter2D,parameter_name='ORM',texture=textures['T_Samurai_ORM'],sampler_type=u.MaterialSamplerType.SAMPLERTYPE_MASKS)
    prop(color,'RGB',u.MaterialProperty.MP_BASE_COLOR); prop(orm,'G',u.MaterialProperty.MP_ROUGHNESS); prop(orm,'B',u.MaterialProperty.MP_METALLIC)
    if not animated:
        normal=expr(mat,u.MaterialExpressionTextureSampleParameter2D,parameter_name='Normal',texture=textures['T_Samurai_Normal'],sampler_type=u.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        prop(normal,'RGB',u.MaterialProperty.MP_NORMAL)
        edit.set_material_usage(mat,u.MaterialUsage.MATUSAGE_SKELETAL_MESH)
    else:
        uv=expr(mat,u.MaterialExpressionTextureCoordinate,coordinate_index=1)
        time=expr(mat,u.MaterialExpressionTime)
        random=expr(mat,u.MaterialExpressionPerInstanceRandom)
        anim=scalar(mat,'AnimationIndex',1); enabled=scalar(mat,'AnimationEnabled',1)
        for kind,property_ in [('Position',u.MaterialProperty.MP_WORLD_POSITION_OFFSET),('Normal',u.MaterialProperty.MP_NORMAL)]:
            tex=expr(mat,u.MaterialExpressionTextureObjectParameter,parameter_name='VAT_'+kind,texture=textures[f'T_VAT_{kind}_LOD0'],sampler_type=u.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
            code='''float clip = clamp(floor(AnimationIndex + 0.5), 0.0, 2.0);
float duration = clip < 0.5 ? 2.0 : (clip < 1.5 ? 1.0 : 1.5);
float frame = frac(Time / duration + Seed) * 24.0;
float a = floor(frame), b = fmod(a + 1.0, 24.0);
// FBX and Unreal flip texture V: the next baked row is below UV.y.
float2 ua = float2(UV.x, UV.y - (clip * 24.0 + a) / 72.0);
float2 ub = float2(UV.x, UV.y - (clip * 24.0 + b) / 72.0);
float3 value = lerp(Texture2DSampleLevel(VAT, VATSampler, ua, 0).xyz,
                    Texture2DSampleLevel(VAT, VATSampler, ub, 0).xyz, frac(frame));
'''
            code += 'return value * AnimationEnabled;' if kind=='Position' else 'return normalize(value * 2.0 - 1.0);'
            custom=expr(mat,u.MaterialExpressionCustom,code=code,output_type=u.CustomMaterialOutputType.CMOT_FLOAT3,description='Actual Blender rig bake • '+kind)
            custom.set_editor_property('inputs',[u.CustomInput(input_name=n) for n in ['VAT','UV','Time','Seed','AnimationIndex','AnimationEnabled']])
            for name,node in [('VAT',tex),('UV',uv),('Time',time),('Seed',random),('AnimationIndex',anim),('AnimationEnabled',enabled)]: link(node,'',custom,name)
            transform=expr(mat,u.MaterialExpressionTransform,transform_source_type=u.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_LOCAL,transform_type=u.MaterialVectorCoordTransform.TRANSFORM_WORLD)
            link(custom,'',transform,'Input')
            if kind=='Normal':
                # Per-vertex IDs must be sampled in vertex stage, then interpolate
                # the resulting normals. Pixel sampling of interpolated IDs is wrong.
                interp=expr(mat,u.MaterialExpressionVertexInterpolator)
                link(transform,'',interp,'Input'); prop(interp,'',property_)
            else: prop(transform,'',property_)
    edit.set_material_usage(mat,u.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES)
    edit.layout_material_expressions(mat); edit.recompile_material(mat)
    u.EditorAssetLibrary.save_loaded_asset(mat)
    return mat
static_mat=atlas_material('M_Samurai_Static',False)
vat_mat=atlas_material('M_SamuraiVAT',True)
instances=[]
for lod in range(3):
    mi=new_asset(f'MI_SamuraiVAT_LOD{lod}',u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
    edit.set_material_instance_parent(mi,vat_mat)
    for kind in ('Position','Normal'): edit.set_material_instance_texture_parameter_value(mi,'VAT_'+kind,textures[f'T_VAT_{kind}_LOD{lod}'])
    edit.set_material_instance_scalar_parameter_value(mi,'AnimationIndex',1)
    edit.set_material_instance_scalar_parameter_value(mi,'AnimationEnabled',1)
    instances.append(mi)

body=import_file(ART/'exports/SK_Samurai01.fbx','SK_Samurai01','skeletal')
body.set_material(0,static_mat)
skeleton=body.get_editor_property('skeleton')
for action in ['A_Neutral','A_Idle','A_Walk','A_Attack']:
    anim=import_file(ART/'exports'/(action+'.fbx'),action,'animation',skeleton)
    if anim.get_editor_property('skeleton')!=skeleton: raise RuntimeError('Wrong animation skeleton')
for name in ['SM_Yumi','SM_Tachi','SM_Sheath','SM_Quiver','SM_Arrows']:
    mesh=import_file(ART/'exports'/(name+'.fbx'),name,'static'); mesh.set_material(0,static_mat)

mesh=import_file(ART/'exports/SM_Samurai01_LOD0.fbx','SM_Samurai01','static')
for lod in (1,2):
    result=stat.import_lod(mesh,lod,str(ART/f'exports/SM_Samurai01_LOD{lod}.fbx'))
    if result!=lod: raise RuntimeError('LOD import failed '+str(lod))
mesh.set_editor_property('static_materials',[u.StaticMaterial(material_interface=mi,material_slot_name=f'LOD{i}') for i,mi in enumerate(instances)])
for lod in range(3):
    stat.set_lod_material_slot(mesh,lod,lod,0)
    settings=stat.get_lod_build_settings(mesh,lod)
    settings.use_full_precision_u_vs=True; settings.generate_lightmap_u_vs=False
    settings.recompute_normals=False; settings.recompute_tangents=False
    stat.set_lod_build_settings(mesh,lod,settings)
stat.set_lod_screen_sizes(mesh,[1.0,.10,.028])
mesh.set_editor_property('positive_bounds_extension',u.Vector(50,50,30))
mesh.set_editor_property('negative_bounds_extension',u.Vector(50,50,10))
# UE's actual reduction backend, same single shared material at all skeletal LODs.
if not skel.regenerate_lod(body,3,False,False): report['warnings'].append('Skeletal automatic LOD generation failed; crowd imported LODs remain valid.')

for name in u.EditorAssetLibrary.list_assets(DEST,recursive=True,include_folder=False):
    obj=u.load_asset(name)
    if obj: u.EditorAssetLibrary.save_loaded_asset(obj,only_if_is_dirty=False)
report['skeletal_body_sections']=[skel.get_num_sections(body,i) for i in range(skel.get_lod_count(body))]
report['skeletal_lod_count']=skel.get_lod_count(body)
report['static_lod_count']=stat.get_lod_count(mesh)
report['static_bounds_cm']={'min':list(mesh.get_bounding_box().min),'max':list(mesh.get_bounding_box().max)}
report['validated']=True
out=ROOT/'artifacts/samurai-prototype/unreal-import.json'; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(report,indent=2)+'\n')
u.log('SHOEN_SAMURAI_IMPORT_VALIDATED '+str(out))
