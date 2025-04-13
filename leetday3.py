class Solution:
    def removeDuplicates(self, nums):
        if not nums:
           return 0

        k = 0
        for i in range(1, len(nums)):
            if nums[i] != nums[k]:
               k += 1
               nums[k] = nums[i]

        return k + 1

sol = Solution()
nums = [1,1,2]
print(sol.removeDuplicates(nums))
print(nums[:2])    