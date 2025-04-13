class Solution:
    def lengthOfLastWord(self, s: str) -> int:

        s = s.rstrip()
        
        if not s:
            return 0

        words=s.split(' ')

        return len(words[-1])
     