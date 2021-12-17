inp=input()
arr=inp.split(' ')
arr=list(map(int,arr))
l_arr=len(arr)
second_large=arr[0]
maximum=second_large
for i in range(1,l_arr):
    if arr[i]>maximum:
        second_large=maximum
        maximum=arr[i]
    elif arr[i]>second_large:
        second_large=arr[i]
print(second_large)

