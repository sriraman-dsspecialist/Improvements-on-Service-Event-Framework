SELECT distinct q.DServiceEventID,
q.Serviceeventcode, q.ServiceEventName, q.AND_OR,
q.Priority, q.confidence, 
q.MaterialGroup, mas.MaterialGroupDescription
from
(SELECT distinct a.DServiceEventID,
    b.Serviceeventcode, b.ServiceEventName, a.AND_OR, 
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