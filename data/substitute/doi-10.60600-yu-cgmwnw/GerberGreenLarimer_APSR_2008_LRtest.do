* Program to evaluate heterogeneous treatment effects in Gerber, Green, and Larimer 2008, pp.39-40
*
* This program is in three parts.  

* Part 1 shows our original work-around to conduct a LR test while avoiding the complications of clustered assignment.
* In this part, we sample 1 subject from each household so that clustering is not an issue.  
* The base model tests the main effects of the four treatment indicators. 
* The alternative model adds interactions with "numvotes" and "hh_size," which amounts to 24 degrees of freedom.  
* The LR test is non-significant (i.e., the null of no interaction with vote propensity cannot be rejected).  
* In order to show the robustness of the result across various random samples, the sampling step is then iteratated, and
* the output displays the p-value given the average chi-square test statistic, which is again non-significant.

* Part 2 anticipates the randomization inference test in Part 3.  It simply shows that the LR test comes out about the same
* when one adds randomly generated treatments to both the base and alternative models, which is what we will do in Part 3.
* It also "shows" that the naive LR test comes up significant when one ignores clustering.

* Part 3 Uses randomization inference to address the nonstandard sampling distribution of the LR test statistic 
* under clustered random assignment. 
* In order to obtain the null reference distribution, faux treatments are randomly assigned by cluster, following 
* the same distribution as the actual treatments.  These faux treatments (called junk*) are
* interacted with numvotes and hh_size, and this alternative model is compared to the null model, with 24 fewer degrees of freedom,
* in which the faux treatments are included but not interacted.  The actual LR test statistic (using the real treatments
* and their interactions) is then compared to this null distribution in order to obtain the p-value.  
* The result is again non-significant (i.e., the null of no interaction with vote propensity cannot be rejected).
*
* Acknowledgement: The authors thank Yi Yin for her programming assistance.

**************************************************************
* PART 1: Randomly sample one person within household clusters
**************************************************************

* load replication data from ISPS archive
*if the do folder is not the current (or active) directory, uncomment the cd command below, specify absolute path of the do folder, and run it to make it the active directory
*cd …/GerberGreenLarimer_APSR_2008
use "GerberGreenLarimer_APSR_2008_social_pressure.dta", clear

* create treatment indicators
xi: logistic voted i.treatment

gen treat1= _Itreatment_1
gen treat2= _Itreatment_2
gen treat3= _Itreatment_3
gen treat4= _Itreatment_4

* note that there are six categories of past vote history (because g2004 is always 1)
gen numvotes= g2000+g2002 +g2004+ p2000+ p2002+ p2004
tab numvotes

* prepare to sample
set seed 123
sample 1,count by(hh_id)

* LR test, avoiding clustering through sampling
* Verify that the number of samples matches the number of household clusters (180,002)
tab hh_size
* recode hh_size because otherwise the number of observations may not be the same across the two regressions
replace hh_size=6 if hh_size > 6

* base model (clustering is irrelevant when one person is sampled per household)
logistic voted treat1 treat2 treat3 treat4 numvotes i.hh_size
estimates store BASE_MODEL

* alternative model with interactions, using 24 more degrees of freedom
xi: logistic voted treat1##c.numvotes treat2##c.numvotes treat3##c.numvotes treat4##c.numvotes treat1##i.hh_size treat2##i.hh_size treat3##i.hh_size treat4##i.hh_size
estimates store ALTERNATIVE_MODEL
lrtest ALTERNATIVE_MODEL BASE_MODEL


****************************************************
*   Repeat samping step to obtain average results
****************************************************
*if the do folder is not the current (or active) directory, uncomment the cd command below, specify absolute path of the do folder, and run it to make it the active directory
*cd …/GerberGreenLarimer_APSR_2008
use "GerberGreenLarimer_APSR_2008_social_pressure.dta", clear

* create treatment indicators
xi: logistic voted i.treatment

gen treat1= _Itreatment_1
gen treat2= _Itreatment_2
gen treat3= _Itreatment_3
gen treat4= _Itreatment_4

* note that there are six categories of past vote history (because g2004 is always 1)
gen numvotes= g2000+g2002 +g2004+ p2000+ p2002+ p2004
tab numvotes


* set the number of replications to be the same as the number of loops
set matsize 10000
cap matrix drop chi2s
matrix chi2s=J(1000, 1, .)


local j = 0
local i = 1
while `i' < 1001 {
	set seed 123`j'
	preserve
	qui sample 1,count by(hh_id)
	qui replace hh_size=6 if hh_size > 6

	* base model (clustering is irrelevant when one person is sampled per household)
	qui logistic voted treat1 treat2 treat3 treat4 numvotes i.hh_size
	local n1 = e(N)
	estimates store BASE_MODEL
	
	* alternative model with interactions, using 24 more degrees of freedom
	qui xi: logistic voted treat1##c.numvotes treat2##c.numvotes treat3##c.numvotes 	treat4##c.numvotes treat1##i.hh_size treat2##i.hh_size treat3##i.hh_size 	treat4##i.hh_size
	local n2 = e(N)
	estimates store ALTERNATIVE_MODEL

	if `n1' == `n2'{
		* di "Results from draw number `i'"
		qui lrtest ALTERNATIVE_MODEL BASE_MODEL
		matrix chi2s[`i',1] = r(chi2) 
		local i = `i' +1
	}
	
	restore	
	local j = `j' +1	
}

*** reports the p-value for the average chi2
preserve
clear
svmat chi2s
summarize chi2s

global avg_chi2 = r(mean)
di "average chi2: " $avg_chi2
disp "p-value: " chi2tail(24, $avg_chi2)
restore

***********************************************************************************************************************
* PART 2: LR Test for the entire subject pool, ignoring clustering, with and without randomly generated junk treatments
***********************************************************************************************************************

* use data from ISPS Archive
*if the do folder is not the current (or active) directory, uncomment the cd command below, specify absolute path of the do folder, and run it to make it the active directory
*cd …/GerberGreenLarimer_APSR_2008
use "GerberGreenLarimer_APSR_2008_social_pressure.dta", clear

xi: logistic voted i.treatment

gen treat1= _Itreatment_1
gen treat2= _Itreatment_2
gen treat3= _Itreatment_3
gen treat4= _Itreatment_4

gen numvotes= g2000+g2002 +g2004+ p2000+ p2002+ p2004

* recode hh_size because otherwise the number of observations may differ across the two regressions due to sparse N
replace hh_size=6 if hh_size > 6
tab hh_size

**** NAIVE LR test that ignores clustering ****

* base model (main effects)
logistic voted treat1 treat2 treat3 treat4 numvotes i.hh_size
estimates store BASE_MODEL_ALL

* alternative model (treatment by numvotes interactions and treatment by hh_size interactions)
xi: logistic voted treat1##c.numvotes treat2##c.numvotes treat3##c.numvotes treat4##c.numvotes treat1##i.hh_size treat2##i.hh_size treat3##i.hh_size treat4##i.hh_size
estimates store ALTERNATIVE_MODEL1

* Note that this test is misleading because it ignores clustered assignment
lrtest ALTERNATIVE_MODEL1 BASE_MODEL_ALL

**** another naive LR test that ignores clustering ****
* This time create faux random treatment assignments at the cluster (hh_id) level.
* Use these random assignments (called junk*) to create faux treatment dummies.
* LR test includes junk variables' MAIN EFFECTS ONLY in BOTH base and alternative models
* ssc install randomizr
set seed 123
cluster_ra Z_clust, cluster_var(hh_id) m_each(100000 20000 20000 20000 20002) replace
gen junk = Z_clust
tab junk
xi: logistic voted i.junk
gen junk1= _Ijunk_2
gen junk2= _Ijunk_3
gen junk3= _Ijunk_4
gen junk4= _Ijunk_5

* LR test under null (adds four junk-treatment dummies)
* base model (main effects)
logistic voted treat1 treat2 treat3 treat4 numvotes i.hh_size junk1 junk2 junk3 junk4
estimates store BASE_MODEL_JUNK

* alternative model (adds junk-treatment dummies and usual interactions between treatment and numvotes and hh_size)
xi: logistic voted  junk1 junk2 junk3 junk4 treat1##c.numvotes treat2##c.numvotes treat3##c.numvotes treat4##c.numvotes treat1##i.hh_size treat2##i.hh_size treat3##i.hh_size treat4##i.hh_size
estimates store ALTERNATIVE_MODEL_JUNK
* Note that this test is misleading because it ignores clustered assignment.
* The point of including it is to show that it generates a test statistic that is trivially different from the preceding LR test.
* The LR test statistic used below in the randomization inference step is the one without junk* indicators.
lrtest ALTERNATIVE_MODEL_JUNK BASE_MODEL_JUNK


*****************************************************************************************************************
* PART 3: LR Test using randomization inference to obtain the proper null distribution under clustered assignment
*****************************************************************************************************************

* use data from ISPS Archive
cd "/Users/dongreen/Dropbox/Social Pressure pubs/ETOV 2006"
use "GerberGreenLarimer_APSR_2008_social_pressure.dta", clear


xi: logistic voted i.treatment

gen treat1= _Itreatment_1
gen treat2= _Itreatment_2
gen treat3= _Itreatment_3
gen treat4= _Itreatment_4

gen numvotes= g2000+g2002 +g2004+ p2000+ p2002+ p2004
* show that there are six categories of past vote history (because g2004 is always 1)
tab numvotes

* recode hh_size because otherwise the number of observations may differ across the two regressions due to sparse N
replace hh_size=6 if hh_size > 6
tab hh_size

**** generate the ACTUAL LR test statistic from the full dataset ****

* base model (main effects)
logistic voted treat1 treat2 treat3 treat4 numvotes i.hh_size
global lrchi1 = e(ll)

* alternative model (treatment by numvotes interactions and treatment by hh_size interactions)
xi: logistic voted treat1##c.numvotes treat2##c.numvotes treat3##c.numvotes treat4##c.numvotes treat1##i.hh_size treat2##i.hh_size treat3##i.hh_size treat4##i.hh_size
global lrchi2 = e(ll)
global true_chi2=2*($lrchi2-$lrchi1)

display 2*($lrchi2-$lrchi1)

**** create null reference distribution of LR test statitics via a loop

gen Z_clust =.
gen junk=. 
gen junk1=.
gen junk2=.
gen junk3=.
gen junk4=.

cap program drop lr_sim
program define lr_sim, rclass
	cluster_ra Z_clust, cluster_var(hh_id) m_each(100000 20000 20000 20000 20002) replace
	replace junk = Z_clust
	qui xi: logistic voted i.junk
	replace junk1= _Ijunk_2
	replace junk2= _Ijunk_3
	replace junk3= _Ijunk_4
	replace junk4= _Ijunk_5
	qui logistic voted treat1 treat2 treat3 treat4 numvotes i.hh_size junk1 junk2 junk3 junk4
	local lr1 = e(ll)	
	qui xi: logistic voted treat1 treat2 treat3 treat4 junk1##c.numvotes junk2##c.numvotes junk3##c.numvotes 	junk4##c.numvotes junk1##i.hh_size junk2##i.hh_size junk3##i.hh_size junk4##i.hh_size 
	local lr2 = e(ll)
	return scalar chi2=2*(`lr2'-`lr1')	
end

* Simulate the null reference distribution with an arbitrary degree of precision depending on "reps"
* Allow some time for procedure to run 
preserve
simulate chi2=r(chi2), reps(1000) seed(123) saving(ri_lr.dta, replace): lr_sim
restore

**** Load null distribution, Calculate p-value and graph the test statistic in relation to the null distribution
use "ri_lr.dta",clear

qui count if chi2 >= $true_chi2
disp "p-value: " r(N)/_N

/*
* display the p-value graphically
graph twoway (histogram chi2,frequency bin(20)) ///
(scatteri 0 $true_chi2 80 $true_chi2, c(l) lc(red) lw(thick) lp(dash) m(i)), ///
legend(off) ///
title("Distribution under the null") ///
xtitle("")
*/

