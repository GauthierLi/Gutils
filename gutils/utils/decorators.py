import time 

def print_run_time(func):  
    def wrapper(*args, **kw):  
        local_time = time.time()  
        result = func(*args, **kw) 
        print(f"""Current Function: [{func.__name__}(args={args}, kwargs={kw})]
    run time is {time.time() - local_time:.2f}""")
        return result
    return wrapper

