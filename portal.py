from tkinter import *
root = Tk()
root.geometry("500x300")

def getvals():
    print("Accepted")

Label(root, text="Python Registration Form", font="arial 15 bold").grid(row=0, column=3)

name = Label(root, text="Name")
cnic = Label(root, text="Cnic")
phone = Label(root, text="Phone")
gender = Label(root, text="Gender")
emergency = Label(root, text="Emergency")
paymentmood = Label(root, text="Payment Mood")

name.grid(row=1, column=2)
cnic.grid(row=2, column=2)
phone.grid(row=3, column=2)
gender.grid(row=4, column=2)
emergency.grid(row=5, column=2)
paymentmood.grid(row=6, column=2)

namevalue = StringVar
cnicvalue = StringVar
phonevalue = StringVar
gendervalue = StringVar
emergencyvalue = StringVar
paymentmathodvalue = StringVar
checkvalue = IntVar


nameentry = Entry(root, textvariable=namevalue )
cnicentry = Entry(root, textvariable=cnicvalue)
phoneentry = Entry(root, textvariable=phonevalue)
genderentry = Entry(root, textvariable=gendervalue)
emergencyentry = Entry(root, textvariable=emergencyvalue)
paymentmathodentry = Entry(root, textvariable=paymentmathodvalue)

nameentry.grid(row=1, column=3)
cnicentry.grid(row=2, column=3)
phoneentry.grid(row=3, column=3)
genderentry.grid(row=4, column=3)
emergencyentry.grid(row=5, column=3)
paymentmathodentry.grid(row=6, column=3)

checkbtn = Checkbutton(text="remember to me!", variable=checkvalue)
checkbtn.grid(row=7, column=3)

Button(text="Submit", command=getvals).grid(row=8, column=3)

root.mainloop()