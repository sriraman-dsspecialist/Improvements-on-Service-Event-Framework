select top 10  * from dim.materialmaster;

-- To retrieve children from parent
SELECT distinct 
b.Material as parent_material, b.MaterialName as parent_material_name,
c.Material as child_material, c.MaterialName as child_material_name
FROM [VPDC].[fct].[MSIComponentV2] a
left join vpdc.dim.MaterialMaster b on a.DMaterialMasterID_Component=b.DMaterialMasterID
left join vpdc.dim.MaterialMaster c on a.DMaterialMasterID_MSI=c.DMaterialMasterID
where b.Material in ('29305524')

--29451396
--29471183
--29327903
--29456873
--29341866
--29350713

-- To retrieve parent from children
SELECT distinct 
c.Material as child_material, c.MaterialName as child_material_name,
b.Material as parent_material, b.MaterialName as parent_material_name
FROM [VPDC].[fct].[MSIComponentV2] a
left join vpdc.dim.MaterialMaster b on a.DMaterialMasterID_Component=b.DMaterialMasterID
left join vpdc.dim.MaterialMaster c on a.DMaterialMasterID_MSI=c.DMaterialMasterID
where c.Material in ('29451396')

			

 