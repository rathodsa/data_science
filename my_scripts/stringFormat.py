from string import Template


def main(name,father):
    str1 = ("This is {0} and my father name is {1}".format((name),(father)))
    print(str1)
    #use the substitute method within the keyword arguments
    tmpl = Template("This the book called ${title} by ${author}")
    str2 = tmpl.substitute(title="The wings of fire", author="APJ")
    print(str2)
    # use the substitute method with a dictionary
    data = {
        "title": "ignited minds",
        "author": "APJ Abdul Kalam"
    }
    str3 = tmpl.substitute(data)
    print(str3)


if __name__ == '__main__':
    name = "Saikrishna"
    father = "Vittal"
    main(name,father)