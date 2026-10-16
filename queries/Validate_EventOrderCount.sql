use vpdc;

select distinct 
tdso.ServiceOrderNumber, soe.DServiceEventID,
tdso.Year, tdso.ServiceOrderText
from scm.tab.dimServiceOrder tdso
join fct.ServiceOrderEvent soe
on tdso.DServiceOrderID	= soe.DServiceOrderID
join dim.ServiceEvent se
on soe.DServiceEventID = se.DServiceEventID	
where se.ServiceEventName = 'Blade Bearing Grease Coupling'
and Year between 2020 and 2026