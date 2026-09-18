SELECT distinct a.DServiceEventID,
    b.Serviceeventcode, b.ServiceEventName,
    Priority, a.confidence,
    value as TaskListGroup 
FROM dim.ServiceEventCriterion a
    CROSS APPLY STRING_SPLIT(TaskListGroup, ',')
    inner join dim.serviceevent b 
	on a.DServiceEventID = b.DServiceEventID
where Serviceeventcode is not null
    and a.isdeleted = 0
    and a.TaskListGroup not like 'N/A';