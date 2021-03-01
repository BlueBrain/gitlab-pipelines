TEMPLATE="""
setup_{what}:
    tags:
      - bb5
    stage: build
    script:
      - echo {who} > {where}.txt
    artifacts:
      paths:
        - {where}.txt

build_{what}:
    stage: build
    needs: [setup_{what}]
    script:
      - for i in $(seq 1 10); do cat {where}.txt >> {where}_again.txt; done
    artifacts:
      paths:
        - {where}_again.txt

test_{what} 1:
    stage: build
    needs: [build_{what}]
    script:
      - cat {where}_again.txt

test_{what} 2:
    stage: build
    needs: [build_{what}]
    script:
      - cat {where}_again.txt

test_{what} 3:
    stage: build
    needs: [build_{what}]
    script:
      - cat {where}_again.txt
"""

for (who, where, what) in (
    ("white", "saloon", "rope"),
    ("green", "kitchen", "chandelier"),
    ("black", "hallway", "revolver"),
    ("red", "office", "knife"),
):
    print(TEMPLATE.format(what=what, where=where, who=who))
