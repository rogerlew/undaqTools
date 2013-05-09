import pstats
p = pstats.Stats('output/profile_results')
p.sort_stats('time').print_stats(100)
