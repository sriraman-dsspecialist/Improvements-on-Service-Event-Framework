use vpdc;

-- 1. Get Service Event x Materials 
Drop table if exists #itemnumber_list;
SELECT distinct q.DServiceEventID,
q.Serviceeventcode, q.ServiceEventName,
q.Priority, q.confidence, 
q.Itemnumber, mas.MaterialName,
mas.MaterialGroup, mas.MaterialGroupDescription
into #itemnumber_list
from
(SELECT distinct a.DServiceEventID,
    b.Serviceeventcode, b.ServiceEventName,
    Priority, a.confidence,
    value as Itemnumber 
FROM dim.ServiceEventCriterion a
    CROSS APPLY STRING_SPLIT(itemnumber, ',')
    inner join dim.serviceevent b 
	on a.DServiceEventID = b.DServiceEventID
where Serviceeventcode is not null
    and a.isdeleted = 0
    and a.itemnumber not like 'N/A')as q
join dim.MaterialMaster mas
on mas.Material = q.itemnumber;

select * from #itemnumber_list;


-- 2.Get Service Event x Material Group : 20s
Drop table if exists #materialgroup_list;
SELECT distinct q.DServiceEventID,
q.Serviceeventcode, q.ServiceEventName,
q.Priority, q.confidence, 
q.MaterialGroup, mas.MaterialGroupDescription
into #materialgroup_list
from
(SELECT distinct a.DServiceEventID,
    b.Serviceeventcode, b.ServiceEventName,
    Priority, a.confidence, 
    value as MaterialGroup
FROM dim.ServiceEventCriterion a
    CROSS APPLY STRING_SPLIT(MaterialGroup, ',')
    inner join dim.serviceevent b 
	on a.DServiceEventID = b.DServiceEventID
where Serviceeventcode is not null
    and a.isdeleted = 0
    and MaterialGroup not like 'N/A')as q
join dim.MaterialMaster mas
on mas.MaterialGroup = q.MaterialGroup;

select * from #materialgroup_list;